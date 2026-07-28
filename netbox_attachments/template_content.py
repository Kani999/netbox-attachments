import logging
from typing import List, Type

from django.db.models import Count
from django.db.utils import OperationalError

from netbox_attachments.utils import (
    _get_plugin_settings,
    custom_object_identifier,
    is_custom_object_model,
    validate_object_type,
)

logger = logging.getLogger(__name__)

ATTACHMENT_PANEL_TEMPLATE = "netbox_attachments/netbox_attachment_panel.html"


def _resolve_display_preference(app_model_name: str, plugin_settings: dict) -> str:
    default_display = plugin_settings.get("display_default", "additional_tab")
    display_settings = plugin_settings.get("display_setting", {})
    if not isinstance(display_settings, dict):
        display_settings = {}
    return display_settings.get(app_model_name, default_display)


def resolve_effective_display_preference(
    app_model_name: str,
    is_custom_object: bool = False,
    plugin_settings: dict | None = None,
) -> str:
    settings_data = _get_plugin_settings() if plugin_settings is None else plugin_settings
    display_preference = _resolve_display_preference(app_model_name, settings_data)

    if is_custom_object and display_preference == "additional_tab":
        return "full_width_page"

    return display_preference


def resolve_display_preference_for_model(model, plugin_settings: dict | None = None) -> str:
    """
    The one model -> effective display position answer, shared by the startup loop and
    the render-time panel so the two cannot drift (issue #112).

    Custom objects are keyed in display_setting by their type name — the same
    identifier scope_filter uses — but resolving that name costs a query, so it is
    looked up only when an override exists that could match. The additional_tab ->
    full_width_page fallback for custom objects lives in
    resolve_effective_display_preference and therefore applies to every caller.
    """
    settings_data = _get_plugin_settings() if plugin_settings is None else plugin_settings
    is_custom_object = is_custom_object_model(model)

    display_key = model._meta.label_lower
    if is_custom_object:
        display_settings = settings_data.get("display_setting")
        if isinstance(display_settings, dict) and display_settings:
            display_key = custom_object_identifier(model) or display_key

    return resolve_effective_display_preference(
        display_key,
        is_custom_object=is_custom_object,
        plugin_settings=settings_data,
    )


def _render_or_empty(extension, template_name: str, label: str, extra_context: dict | None = None) -> str:
    """Render a template on a PluginTemplateExtension, degrading to '' on any failure."""
    try:
        return extension.render(template_name, extra_context=extra_context)
    except Exception as exc:
        logger.error(f"Failed to render {template_name} for {label}: {exc}")
        return ""


def render_attachment_panel(self) -> str:
    model_name = self.models[0] if (hasattr(self, "models") and self.models) else getattr(self, "model", None)
    if model_name is None:
        logger.error("No model or models attribute found on extension")
        return ""
    if "." not in str(model_name):
        logger.error(f"Invalid model name format: {model_name!r}")
        return ""
    return _render_or_empty(self, ATTACHMENT_PANEL_TEMPLATE, str(model_name))


def create_add_attachment_button(model_name: str, url_pattern_name: str):
    from netbox.plugins import PluginTemplateExtension

    class AddAttachmentButton(PluginTemplateExtension):
        models = [model_name]

        def buttons(self):
            return _render_or_empty(
                self,
                "netbox_attachments/add_attachment_button.html",
                model_name,
                extra_context={"object_type_attachment_list": url_pattern_name},
            )

    return AddAttachmentButton


def register_attachment_tab_view(model) -> str:
    from core.models.object_types import ObjectType
    from netbox.context import current_request
    from netbox.views import generic
    from utilities.views import ViewTab, register_model_view

    from netbox_attachments import filtersets, tables
    from netbox_attachments.models import NetBoxAttachment, NetBoxAttachmentAssignment

    model_name = model._meta.model_name
    view_name = f"{model_name}-attachment_list"
    view_path = view_name

    class AttachmentTabView(generic.ObjectChildrenView):
        queryset = model.objects.all()
        child_model = NetBoxAttachmentAssignment
        table = tables.NetBoxAttachmentForObjectTable
        filterset = filtersets.NetBoxAttachmentAssignmentFilterSet
        template_name = "netbox_attachments/generic_tab_list.html"
        actions = ()  # per-row unlink button handles deletion; no bulk URLs registered

        tab = ViewTab(
            label="Attachments",
            badge=lambda obj: (
                NetBoxAttachment.objects.filter(
                    attachment_assignments__object_type=ObjectType.objects.get_for_model(obj),
                    attachment_assignments__object_id=obj.id,
                )
                .restrict(current_request.get().user, "view")
                .distinct()
                .count()
            ),
            hide_if_empty=False,
            permission="netbox_attachments.view_netboxattachment",
        )

        def get_children(self, request, parent):
            return (
                NetBoxAttachmentAssignment.objects.filter(
                    object_type=ObjectType.objects.get_for_model(parent),
                    object_id=parent.id,
                )
                .restrict(request.user, "view")
                .select_related("attachment")
                .prefetch_related("tags", "attachment__tags")
                .annotate(attachment_link_count=Count("attachment__attachment_assignments", distinct=True))
            )

    register_model_view(model, name=view_name, path=view_path)(AttachmentTabView)

    return view_name


def render_custom_object_panel(extension, position: str) -> str:
    """
    Render the attachment panel for `position` if the object in context is an in-scope
    custom object configured to display there; otherwise return an empty string.

    Ordered cheapest-check-first: a global extension is offered every object in NetBox,
    so non-custom-object pages must exit on a string compare before any settings or
    database work. The CustomObjectType name lookups further down are cached per
    generated class (see custom_object_identifier).
    """
    obj = extension.context.get("object")
    model = type(obj)
    # NetBox hands global extensions whatever is in context — None, a non-model, or
    # even a model class (whose type() is the metaclass). Everything downstream reads
    # the CLASS's _meta, so that is what must exist; checking obj._meta instead would
    # let a model class through and crash on ModelBase._meta.
    if not hasattr(model, "_meta"):
        return ""

    if not is_custom_object_model(model):
        return ""

    if resolve_display_preference_for_model(model) != position:
        return ""

    if not validate_object_type(model):
        return ""

    return _render_or_empty(extension, ATTACHMENT_PANEL_TEMPLATE, model._meta.label_lower)


def create_custom_object_attachment_panel():
    """
    Build the globally registered extension that renders attachment panels on custom
    object detail pages.

    Custom object models cannot be enumerated at import time: netbox_custom_objects
    withholds its dynamic models until its own ready() has finished, and plugin ready()
    order follows PLUGINS, so they are absent whenever this plugin loads first (issue
    #110). Registering with models = None defers the decision to render time, when the
    models reliably exist — which also lets object types created after startup work
    without a NetBox restart.
    """
    from netbox.plugins import PluginTemplateExtension

    class CustomObjectAttachmentPanel(PluginTemplateExtension):
        models = None

        def left_page(self):
            return render_custom_object_panel(self, "left_page")

        def right_page(self):
            return render_custom_object_panel(self, "right_page")

        def full_width_page(self):
            return render_custom_object_panel(self, "full_width_page")

    return CustomObjectAttachmentPanel


def get_template_extensions() -> List[Type]:
    try:
        from django.apps import apps
        from netbox.plugins import PluginTemplateExtension

        _ = PluginTemplateExtension
    except Exception:
        return []

    # Registered up front so custom object support survives any failure below: it
    # enumerates no models and touches no database. Self-gating, so it is also safe
    # to register without netbox_custom_objects installed.
    extensions = [create_custom_object_attachment_panel()]

    try:
        plugin_settings = _get_plugin_settings()
        should_add_button = plugin_settings.get("create_add_button", True)

        if not isinstance(should_add_button, bool):
            logger.warning("Invalid create_add_button value, defaulting to True")
            should_add_button = True

        # Custom objects are deliberately not collected here; CustomObjectAttachmentPanel
        # handles them at render time.
        all_models = list(apps.get_models())
        logger.debug(f"Found {len(all_models)} standard Django models")

        seen_models = set()
        unique_models = []
        for model in all_models:
            model_id = model._meta.label_lower
            if model_id not in seen_models:
                seen_models.add(model_id)
                unique_models.append(model)

        if len(all_models) != len(unique_models):
            logger.debug(
                f"Deduplicated models: {len(all_models)} -> {len(unique_models)} "
                f"(removed {len(all_models) - len(unique_models)} duplicates)"
            )

        for model in unique_models:
            # When netbox_custom_objects loads first its dynamic models are already in
            # apps.get_models(); a per-model extension here would render a second panel
            # alongside the global one, and the additional_tab branch below must never
            # see them (their detail pages cannot host tabs or top buttons).
            # Consolidating the two mechanisms is tracked in issue #112.
            if is_custom_object_model(model):
                continue

            if not validate_object_type(model):
                continue

            app_label = model._meta.app_label
            model_name = model._meta.model_name
            app_model_name = model._meta.label_lower

            display_preference = resolve_display_preference_for_model(model, plugin_settings=plugin_settings)

            if display_preference == "additional_tab":
                view_name = register_attachment_tab_view(model)

                if should_add_button:
                    url_pattern_name = f"{app_label}:{model_name}_{view_name}"
                    extensions.append(create_add_attachment_button(app_model_name, url_pattern_name))
                continue

            from netbox.plugins import PluginTemplateExtension

            extension_name = f"{app_label}_{model_name}_attachment_extension"
            extension_class = type(
                extension_name,
                (PluginTemplateExtension,),
                {
                    "models": [app_model_name],
                    display_preference: render_attachment_panel,
                },
            )

            extensions.append(extension_class)

    except OperationalError:
        logger.error("Database is not ready, skipping template extensions setup")
    except Exception as e:
        logger.error("Unexpected error in template extensions setup")
        logger.debug(f"Error details: {str(e)}", exc_info=True)

    return extensions


template_extensions = get_template_extensions()
