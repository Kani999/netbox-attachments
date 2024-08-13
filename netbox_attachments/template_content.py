import logging

from core.models.contenttypes import ObjectType
from django.apps import apps
from django.conf import settings
from django.db.utils import OperationalError
from netbox.context import current_request
from netbox.plugins import PluginTemplateExtension
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from netbox_attachments import filtersets, tables
from netbox_attachments.models import NetBoxAttachment

plugin_settings = settings.PLUGINS_CONFIG.get("netbox_attachments", {})


def create_attachments_panel(self):
    app_label, _ = self.model.split(".")
    try:
        return self.render("netbox_attachments/netbox_attachment_panel.html")
    except ObjectType.DoesNotExist:
        logging.error(f"ObjectType for {app_label} {self.model} does not exist")
        return ""


def get_display_on(app_model_name):
    """Get prefered display setting (left_page, right_page, full_width_page, additional_tab) for attachment panel

    Args:
        app_model_name (str): <app_label>.<model> = (dcim.device, ipam.vlan, ...)

    Returns:
        str: Configured display setting or default
    """
    # set default
    display_on = plugin_settings.get("display_default", "additional_tab")

    # Find configured display setting or return default
    if display_setting := plugin_settings.get("display_setting"):
        display_on = display_setting.get(app_model_name, display_on)

    return display_on


def create_add_button(model_name):
    """Creates add attachment button

    Args:
        model_name (str): <app_label>.<model> = (dcim.device, ipam.vlan, ...)

    Returns:
        Button: Add attachment button at the top of model
    """

    class Button(PluginTemplateExtension):
        model = model_name

        def buttons(self):
            return self.render("netbox_attachments/add_attachment_button.html")

    return Button


def create_tab_view(model):
    """Creates attachment tab. Append it to the passed model

    Args:
        model (Object): Model representation
    """
    name = f"{model._meta.model_name}-attachment_list"
    path = f"{model._meta.model_name}-attachment_list"

    class View(generic.ObjectChildrenView):
        def __init__(self, *args, **kwargs):
            self.queryset = model.objects.all()
            self.child_model = NetBoxAttachment
            self.table = tables.NetBoxAttachmentTable
            self.filterset = filtersets.NetBoxAttachmentFilterSet
            self.template_name = "netbox_attachments/generic_tab_list.html"
            super().__init__(*args, **kwargs)

        table = tables.NetBoxAttachmentTable
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
            childrens = self.child_model.objects.filter(
                object_type=ObjectType.objects.get_for_model(parent),
                object_id=parent.id,
            ).restrict(request.user, "view")
            return childrens

    register_model_view(model, name=name, path=path)(View)


# Generate plugin extension for all classes
def get_templates_extensions():
    template_extensions = []

    try:
        # Iterate over all NetBox models
        for model in apps.get_models():
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            app_model_name = f"{app_label}.{model_name}"

            # Skip if app is not present in configuration
            if app_label not in plugin_settings.get("apps"):
                continue

            # Load prefeed display setting and model class
            display = get_display_on(app_model_name)

            # Special case - if display setting is set as additional_tab
            # https://docs.netbox.dev/en/stable/plugins/development/views/#additional-tabs
            if display == "additional_tab" and model:
                # create add attachment button at the top of the parent view
                template_extensions.append(create_add_button(app_model_name))
                # add attachment tab to the parent view
                create_tab_view(model)
                continue

            # Otherwise create panels and tweak them to the configured location (left, right, full_width_page)
            klass_name = f"{app_label}_{model}_plugin_template_extension"
            dynamic_klass = type(
                klass_name,
                (PluginTemplateExtension,),
                {"model": app_model_name, display: create_attachments_panel},
            )

            template_extensions.append(dynamic_klass)
    except OperationalError as e:
        logging.error("Database is not ready")
        logging.debug(e)
    except Exception as e:
        logging.error("Unexpected error - netbox-attachments won't be rendered")
        logging.debug(e)

    return template_extensions


template_extensions = get_templates_extensions()
