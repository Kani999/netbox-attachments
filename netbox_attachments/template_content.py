import logging
from typing import List, Type

from django.db.models import Count
from django.db.utils import OperationalError

from netbox_attachments.utils import _get_plugin_settings, is_custom_object_model, validate_object_type

logger = logging.getLogger(__name__)


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


def render_attachment_panel(self) -> str:
    model_name = self.models[0] if (hasattr(self, "models") and self.models) else getattr(self, "model", None)
    if model_name is None:
        logger.error("No model or models attribute found on extension")
        return ""
    if "." not in str(model_name):
        logger.error(f"Invalid model name format: {model_name!r}")
        return ""
    try:
        return self.render("netbox_attachments/netbox_attachment_panel.html")
    except Exception as exc:
        logger.error(f"Failed to render attachment panel for {model_name}: {exc}")
        return ""


def get_display_preference(app_model_name: str) -> str:
    return _resolve_display_preference(app_model_name, _get_plugin_settings())


def create_add_attachment_button(model_name: str, url_pattern_name: str):
    from netbox.plugins import PluginTemplateExtension

    class AddAttachmentButton(PluginTemplateExtension):
        models = [model_name]

        def buttons(self):
            try:
                return self.render(
                    "netbox_attachments/add_attachment_button.html",
                    extra_context={"object_type_attachment_list": url_pattern_name},
                )
            except Exception as e:
                logger.error(f"Failed to render add attachment button for {model_name}: {e}")
                return ""

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


def discover_custom_object_models():
    try:
        from django.apps import apps

        custom_objects_app = apps.get_app_config("netbox_custom_objects")
        all_models = list(custom_objects_app.get_models())

        logger.debug(f"Found {len(all_models)} total models in netbox_custom_objects app")

        custom_object_models = [m for m in all_models if is_custom_object_model(m)]

        logger.info(f"Discovered {len(custom_object_models)} custom object models for attachments")

        return custom_object_models

    except LookupError:
        logger.info("NetBox Custom Objects plugin not found - custom objects support disabled")
        return []
    except ImportError as e:
        logger.warning(f"Could not import netbox_custom_objects: {e}")
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error discovering custom object models: {e}",
            exc_info=True,
        )
        return []


def get_template_extensions() -> List[Type]:
    try:
        from django.apps import apps
        from netbox.plugins import PluginTemplateExtension

        _ = PluginTemplateExtension
    except Exception:
        return []

    extensions = []

    try:
        plugin_settings = _get_plugin_settings()
        should_add_button = plugin_settings.get("create_add_button", True)

        if not isinstance(should_add_button, bool):
            logger.warning("Invalid create_add_button value, defaulting to True")
            should_add_button = True

        all_models = list(apps.get_models())
        logger.debug(f"Found {len(all_models)} standard Django models")

        custom_object_models = discover_custom_object_models()
        if custom_object_models:
            all_models.extend(custom_object_models)
            logger.info(f"Added {len(custom_object_models)} custom object models to processing queue")

        seen_models = set()
        unique_models = []
        for model in all_models:
            model_id = f"{model._meta.app_label}.{model._meta.model_name}"
            if model_id not in seen_models:
                seen_models.add(model_id)
                unique_models.append(model)

        if len(all_models) != len(unique_models):
            logger.debug(
                f"Deduplicated models: {len(all_models)} -> {len(unique_models)} "
                f"(removed {len(all_models) - len(unique_models)} duplicates)"
            )

        for model in unique_models:
            if not validate_object_type(model):
                continue

            app_label = model._meta.app_label
            model_name = model._meta.model_name
            app_model_name = f"{app_label}.{model_name}"

            display_preference = resolve_effective_display_preference(
                app_model_name,
                is_custom_object=is_custom_object_model(model),
                plugin_settings=plugin_settings,
            )

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
