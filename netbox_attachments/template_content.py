import logging
from typing import List, Type

from core.models.object_types import ObjectType
from django.apps import apps
from django.conf import settings
from django.db.models import Model
from django.db.utils import OperationalError
from netbox.context import current_request
from netbox.plugins import PluginTemplateExtension
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from netbox_attachments import filtersets, tables
from netbox_attachments.models import NetBoxAttachment
from netbox_attachments.utils import is_custom_object_model, validate_object_type

logger = logging.getLogger(__name__)
PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netbox_attachments", {})


def render_attachment_panel(self) -> str:
    """
    Renders the attachment panel template for a model.

    Args:
        self: The plugin template extension instance

    Returns:
        str: Rendered HTML content or empty string if rendering fails
    """
    model_name = self.models[0] if hasattr(self, "models") else self.model

    app_label, _ = model_name.split(".")
    try:
        return self.render("netbox_attachments/netbox_attachment_panel.html")
    except ObjectType.DoesNotExist:
        logger.error(f"ObjectType for {app_label} {self.model} does not exist")
        return ""


def get_display_preference(app_model_name: str) -> str:
    """
    Get preferred display setting for attachment panel.

    Args:
        app_model_name: String in format "<app_label>.<model>" (e.g., "dcim.device")

    Returns:
        str: Display setting value (left_page, right_page, full_width_page, or additional_tab)
    """
    # Set default from plugin settings or fallback to additional_tab
    default_display = PLUGIN_SETTINGS.get("display_default", "additional_tab")

    # Find configured display setting or return default
    display_settings = PLUGIN_SETTINGS.get("display_setting", {})
    return display_settings.get(app_model_name, default_display)


def create_add_attachment_button(model_name: str, url_pattern_name: str) -> Type[PluginTemplateExtension]:
    """
    Creates an 'add attachment' button extension for a model.

    Args:
        model_name: String in format "<app_label>.<model>" (e.g., "dcim.device")
        url_pattern_name: Fully qualified URL pattern name for the attachment list view
            (e.g., "dcim:device_device-attachment_list")

    Returns:
        Type[PluginTemplateExtension]: Button extension class
    """

    class AddAttachmentButton(PluginTemplateExtension):
        models = [model_name]

        def buttons(self):
            try:
                return self.render(
                    "netbox_attachments/add_attachment_button.html",
                    extra_context={'object_type_attachment_list': url_pattern_name}
                )
            except Exception as e:
                logger.error(f"Failed to render add attachment button for {model_name}: {e}")
                return ""

    return AddAttachmentButton


def register_attachment_tab_view(model: Type[Model]) -> str:
    """
    Creates and registers an attachment tab view for a model.

    Args:
        model: Django model class to add the tab view to

    Returns:
        str: name of the registered view
    """
    model_name = model._meta.model_name
    view_name = f"{model_name}-attachment_list"
    view_path = view_name  # Path matches the name

    class AttachmentTabView(generic.ObjectChildrenView):
        queryset = model.objects.all()
        child_model = NetBoxAttachment
        table = tables.NetBoxAttachmentTable
        filterset = filtersets.NetBoxAttachmentFilterSet
        template_name = "netbox_attachments/generic_tab_list.html"

        tab = ViewTab(
            label="Attachments",
            badge=lambda obj: NetBoxAttachment.objects.filter(
                object_type=ObjectType.objects.get_for_model(obj),
                object_id=obj.id,
            )
            .restrict(current_request.get().user, "view")
            .count(),
            hide_if_empty=False,
            permission="netbox_attachments.view_netboxattachment",
        )

        def get_children(self, request, parent):
            return NetBoxAttachment.objects.filter(
                object_type=ObjectType.objects.get_for_model(parent),
                object_id=parent.id,
            ).restrict(request.user, "view")

    register_model_view(model, name=view_name, path=view_path)(AttachmentTabView)

    return view_name


def discover_custom_object_models():
    """
    Discovers dynamically created NetBox Custom Objects models.

    Attempts to load the netbox_custom_objects app and retrieve its models,
    which include both regular plugin models and dynamically created custom
    object models. Returns an empty list if the plugin is not installed or
    encounters errors.

    Returns:
        List[Type[Model]]: List of custom object models, or empty list if unavailable
    """
    try:
        custom_objects_app = apps.get_app_config('netbox_custom_objects')

        # Get all models from the app (includes both regular and dynamic models)
        all_models = list(custom_objects_app.get_models())

        logger.debug(
            f"Found {len(all_models)} total models in netbox_custom_objects app"
        )

        # Filter to only include actual custom object models
        custom_object_models = [m for m in all_models if is_custom_object_model(m)]

        logger.info(
            f"Discovered {len(custom_object_models)} custom object models for attachments"
        )

        return custom_object_models

    except LookupError:
        logger.info(
            "NetBox Custom Objects plugin not found - custom objects support disabled"
        )
        return []
    except ImportError as e:
        logger.warning(
            f"Could not import netbox_custom_objects: {e}"
        )
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error discovering custom object models: {e}",
            exc_info=True
        )
        return []


def get_template_extensions() -> List[Type[PluginTemplateExtension]]:
    """
    Generates template extension classes for eligible models.

    Iterates through all registered Django models (including custom object models),
    validates each for eligibility, and determines its display preference from the
    plugin settings. If the preference is "additional_tab", the function registers
    an attachment tab view and optionally adds an "add attachment" button.
    Otherwise, it creates a panel extension class that renders an attachment panel.

    Custom object models from the netbox_custom_objects plugin are discovered
    separately and processed using the same validation and registration logic.

    Database operational errors and unexpected exceptions are logged without
    interrupting the extension generation process.

    Returns:
        List[Type[PluginTemplateExtension]]: A list of dynamically created template extension classes.
    """
    extensions = []

    try:
        # Extract plugin settings with defaults
        should_add_button = PLUGIN_SETTINGS.get("create_add_button", False)

        if not isinstance(should_add_button, bool):
            logger.warning("Invalid create_add_button value, defaulting to False")
            should_add_button = False

        # Collect all models to process
        all_models = []

        # Add standard Django models
        standard_models = list(apps.get_models())
        all_models.extend(standard_models)
        logger.debug(f"Found {len(standard_models)} standard Django models")

        # Add custom object models if enabled
        custom_object_models = discover_custom_object_models()
        if custom_object_models:
            all_models.extend(custom_object_models)
            logger.info(
                f"Added {len(custom_object_models)} custom object models to processing queue"
            )

        # Deduplicate models by their unique identifier (app_label.model_name)
        # This prevents duplicate template extensions for the same model
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

        # Process each model
        for model in unique_models:
            if not validate_object_type(model):
                continue

            app_label = model._meta.app_label
            model_name = model._meta.model_name
            app_model_name = f"{model._meta.app_label}.{model._meta.model_name}"

            # Get display preference for this model
            display_preference = get_display_preference(app_model_name)

            # Check if this is a custom object model
            is_custom_obj = is_custom_object_model(model)

            # Custom objects don't support additional_tab due to non-standard URL routing
            # Force them to use full_width_page instead
            if is_custom_obj and display_preference == "additional_tab":
                logger.info(
                    f"Custom object {app_model_name} forced to full_width_page display "
                    "(additional_tab not supported for custom objects)"
                )
                display_preference = "full_width_page"

            # Handle display as additional tab
            if display_preference == "additional_tab":
                # Register tab view
                view_name = register_attachment_tab_view(model)

                # Add button if configured
                if should_add_button:
                    url_pattern_name = f"{app_label}:{model_name}_{view_name}"
                    extensions.append(create_add_attachment_button(app_model_name, url_pattern_name))

                continue

            # Create panel extension in the specified location
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


# Generate all template extensions
template_extensions = get_template_extensions()
