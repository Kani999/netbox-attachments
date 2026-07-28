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
    The one model -> effective display position answer, shared by the startup loop
    (additional_tab) and the render-time panel (all positions).

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


def render_panel(extension, position: str) -> str:
    """
    Render the attachment panel for `position` when the object in context is an in-scope
    model whose effective display preference is `position`; otherwise return ''.

    Serves standard and custom models alike. Checks run cheapest-first: the display
    resolution bails on a string compare before validate_object_type, the only step
    that can hit the database.
    """
    obj = extension.context.get("object")
    model = type(obj)
    # Context may hold None, a non-model, or a model class (whose type() is the
    # metaclass); everything below reads the class's _meta, so guard that.
    if not hasattr(model, "_meta"):
        return ""

    if resolve_display_preference_for_model(model) != position:
        return ""

    if not validate_object_type(model):
        return ""

    return _render_or_empty(extension, ATTACHMENT_PANEL_TEMPLATE, model._meta.label_lower)


def create_attachment_panel():
    """
    Global extension (models = None) that renders attachment panels at request time.

    Deferring to render time keeps it independent of PLUGINS load order and picks up
    custom object types created after startup — neither of which a startup-time model
    enumeration can do.
    """
    from netbox.plugins import PluginTemplateExtension

    class AttachmentPanel(PluginTemplateExtension):
        models = None

        def left_page(self):
            return render_panel(self, "left_page")

        def right_page(self):
            return render_panel(self, "right_page")

        def full_width_page(self):
            return render_panel(self, "full_width_page")

    return AttachmentPanel


def get_template_extensions() -> List[Type]:
    try:
        from django.apps import apps
        from netbox.plugins import PluginTemplateExtension

        _ = PluginTemplateExtension
    except Exception:
        return []

    # Registered up front so the render-time panel survives any failure below: it
    # enumerates no models, touches no database, and self-gates per request.
    extensions = [create_attachment_panel()]

    try:
        plugin_settings = _get_plugin_settings()
        should_add_button = plugin_settings.get("create_add_button", True)

        if not isinstance(should_add_button, bool):
            logger.warning("Invalid create_add_button value, defaulting to True")
            should_add_button = True

        # This loop only registers additional_tab tabs, which must exist at startup;
        # side/full-width panels are served at request time by the render-time panel.
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
            # Custom objects are served entirely at render time and can never use
            # additional_tab, so skip them here — this also keeps startup free of
            # custom-object DB access and PLUGINS-order dependence.
            if is_custom_object_model(model):
                continue

            if not validate_object_type(model):
                continue

            if resolve_display_preference_for_model(model, plugin_settings=plugin_settings) != "additional_tab":
                continue

            app_label = model._meta.app_label
            model_name = model._meta.model_name
            app_model_name = model._meta.label_lower
            view_name = register_attachment_tab_view(model)

            if should_add_button:
                url_pattern_name = f"{app_label}:{model_name}_{view_name}"
                extensions.append(create_add_attachment_button(app_model_name, url_pattern_name))

    except OperationalError:
        logger.error("Database is not ready, skipping template extensions setup")
    except Exception as e:
        logger.error("Unexpected error in template extensions setup")
        logger.debug(f"Error details: {str(e)}", exc_info=True)

    return extensions


template_extensions = get_template_extensions()
