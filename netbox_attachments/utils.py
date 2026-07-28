from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist


def _get_plugin_settings():
    try:
        plugins_config = getattr(settings, "PLUGINS_CONFIG", {})
    except (AttributeError, ImproperlyConfigured):
        return {}

    if not isinstance(plugins_config, dict):
        return {}

    plugin_settings = plugins_config.get("netbox_attachments", {})
    if not isinstance(plugin_settings, dict):
        return {}

    return plugin_settings


def choice_default(value, choices, default=None):
    """Return value if it is among choices, else default."""
    if value not in choices:
        return default
    return value


def attachment_upload(instance, filename):
    """
    Build an attachment's upload path under the fixed "netbox-attachments/" prefix.

    An instance name that differs from the uploaded filename renames the file, keeping
    the original extension(s).
    """
    path = "netbox-attachments/"

    if instance.name and instance.name != filename:
        extension = "".join(Path(filename).suffixes)
        filename = "".join([Path(instance.name).name, extension])  # strip dir components

    return "{}{}".format(path, Path(filename).name)


def is_custom_object_model(model):
    """
    True for a netbox_custom_objects dynamic model.

    CustomObject subclasses only, which excludes the plugin's own metadata models
    (CustomObjectType, CustomObjectTypeField, ...) living in the same app.
    """
    if model._meta.app_label != "netbox_custom_objects":
        return False

    try:
        from netbox_custom_objects.models import CustomObject

        return issubclass(model, CustomObject) and model is not CustomObject and not model._meta.abstract
    except (ImportError, AttributeError):
        return False


def custom_object_identifier(model):
    """
    Return the config identifier for a custom object model, or None if unresolvable.

    Custom object models are named after their backing table's primary key
    ("table134model"), which is opaque and differs between installs, so settings key off
    the Custom Object Type's name instead: "netbox_custom_objects.cotab2_asset". Both
    scope_filter and display_setting must use this, or one of them silently never matches.
    """
    if not is_custom_object_model(model):
        return None

    return _resolve_custom_object_identifier(model)


@lru_cache(maxsize=256)
def _resolve_custom_object_identifier(model):
    """
    CustomObjectType lookup, cached per generated model class.

    The scope check and the display-key resolution can each need this during one page
    render; uncached that is repeated identical queries. Caching on the class is sound
    because netbox_custom_objects regenerates the dynamic class whenever its
    CustomObjectType is saved (a rename means a new class object, i.e. a new cache
    key). A queryset .update() bypasses that signal and would serve a stale name until
    restart — the same tradeoff the CO plugin's own model cache makes. Only custom
    object classes reach this (the public wrapper filters), so standard models never
    churn the LRU.
    """
    try:
        from netbox_custom_objects.models import CustomObjectType

        cot = CustomObjectType.objects.get(id=model.custom_object_type_id)
    except (ImportError, AttributeError, ObjectDoesNotExist):
        return None

    return f"{model._meta.app_label}.{cot.name}"


def validate_object_type(model):
    """
    Whether the model is permitted to have attachments, per scope_filter/applied_scope.

    In 'model' scope the filter is mixed: a bare app label ('dcim') enables every model in
    that app, an exact identifier ('dcim.device') enables only that one. Custom objects are
    matched by their CustomObjectType name, not their generated class name — see
    custom_object_identifier.
    """
    plugin_settings = _get_plugin_settings()
    applied_scope = choice_default(plugin_settings.get("applied_scope"), ("app", "model"), "app")
    scope_filter = plugin_settings.get("scope_filter")
    if scope_filter is None or not isinstance(scope_filter, (list, tuple, set)):
        scope_filter = []

    app_label = model._meta.app_label

    if applied_scope == "app":
        # App mode: only app_label matters — no DB access needed.
        return app_label in scope_filter

    elif applied_scope == "model":
        # Short-circuit on app_label first (no DB access needed).
        if app_label in scope_filter:
            return True
        # Need model_identifier for the specific-model check.
        # For custom objects this resolves via DB, so it runs only when necessary.
        if is_custom_object_model(model):
            model_identifier = custom_object_identifier(model)
            if model_identifier is None:
                return False
        else:
            model_identifier = model._meta.label_lower
        return model_identifier in scope_filter

    return False


def get_enabled_object_type_queryset():
    """
    Returns an ObjectType queryset limited to models enabled in the plugin config.
    Used by the link form to restrict the object type picker to valid choices.
    """
    from functools import reduce
    from operator import or_

    from django.apps import apps
    from django.db.models import Q

    from core.models.object_types import ObjectType

    q_filters = []
    seen = set()

    # Standard models
    for model in apps.get_models():
        key = model._meta.label_lower
        if key in seen:
            continue
        seen.add(key)
        if validate_object_type(model):
            q_filters.append(Q(app_label=model._meta.app_label, model=model._meta.model_name))

    # Custom objects (gracefully absent if plugin not installed)
    try:
        custom_app = apps.get_app_config("netbox_custom_objects")
        for model in custom_app.get_models():
            key = model._meta.label_lower
            if key in seen:
                continue
            seen.add(key)
            if validate_object_type(model):
                q_filters.append(Q(app_label=model._meta.app_label, model=model._meta.model_name))
    except (LookupError, ImportError):
        pass

    if not q_filters:
        return ObjectType.objects.none()

    return ObjectType.objects.filter(reduce(or_, q_filters))
