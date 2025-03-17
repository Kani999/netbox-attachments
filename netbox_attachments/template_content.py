import logging
from typing import List, Type

from core.models.contenttypes import ObjectType
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
from netbox_attachments.utils import validate_object_type

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
    app_label, _ = self.model.split(".")
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


def create_add_attachment_button(model_name: str) -> Type[PluginTemplateExtension]:
    """
    Creates an 'add attachment' button extension for a model.

    Args:
        model_name: String in format "<app_label>.<model>" (e.g., "dcim.device")

    Returns:
        Type[PluginTemplateExtension]: Button extension class
    """

    class AddAttachmentButton(PluginTemplateExtension):
        model = model_name

        def buttons(self):
            return self.render("netbox_attachments/add_attachment_button.html")

    return AddAttachmentButton


def register_attachment_tab_view(model: Type[Model]) -> None:
    """
    Creates and registers an attachment tab view for a model.

    Args:
        model: Django model class to add the tab view to
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


def get_template_extensions() -> List[Type[PluginTemplateExtension]]:
    """
    Generates template extension classes for eligible models.

    Iterates through all registered Django models, validates each for eligibility, and determines
    its display preference from the plugin settings. If the preference is "additional_tab", the
    function registers an attachment tab view and optionally adds an "add attachment" button.
    Otherwise, it creates a panel extension class that renders an attachment panel. Database
    operational errors and unexpected exceptions are logged without interrupting the extension
    generation process.

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

        # Process each model
        for model in apps.get_models():
            if not validate_object_type(model):
                continue

            app_label = model._meta.app_label
            model_name = model._meta.model_name
            app_model_name = f"{model._meta.app_label}.{model._meta.model_name}"

            # Get display preference for this model
            display_preference = get_display_preference(app_model_name)

            # Handle display as additional tab
            if display_preference == "additional_tab":
                # Add button if configured
                if should_add_button:
                    extensions.append(create_add_attachment_button(app_model_name))

                # Register tab view
                register_attachment_tab_view(model)
                continue

            # Create panel extension in the specified location
            extension_name = f"{app_label}_{model_name}_attachment_extension"
            extension_class = type(
                extension_name,
                (PluginTemplateExtension,),
                {"model": app_model_name, display_preference: render_attachment_panel},
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
