import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.utils import OperationalError
from extras.plugins import PluginTemplateExtension
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from . import filtersets, models, tables
from .models import NetBoxAttachment

plugin_settings = settings.PLUGINS_CONFIG.get('netbox_attachments', {})
template_extensions = []


def create_attachments_panel(self):
    obj = self.context['object']
    app_label, model = self.model.split(".")
    content_type_id = ContentType.objects.get(app_label=app_label,
                                              model=model).id

    return self.render(
        'netbox_attachments/netbox_attachment_panel.html',
        extra_context={
            'netbox_attachments': NetBoxAttachment.objects.filter(content_type_id=content_type_id,
                                                                  object_id=obj.id),
        }
    )


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
    if display_setting := plugin_settings.get('display_setting'):
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
            return self.render('netbox_attachments/add_attachment_button.html')

    return Button


def create_tab_view(model, base_template_name="generic/object.html"):
    """Creates attachment tab. Append it to the passed model

    Args:
        model (Object): Model representation
    """
    name = f"{model._meta.model_name}-attachment_list"
    path = f"{model._meta.model_name}-attachment_list"

    class View(generic.ObjectChildrenView):
        def __init__(self, *args, **kwargs):
            self.queryset = model.objects.all()
            self.child_model = models.NetBoxAttachment
            self.table = tables.NetBoxAttachmentTable
            self.filterset = filtersets.NetBoxAttachmentFilterSet
            self.template_name = "netbox_attachments/generic_tab_list.html"
            super().__init__(*args, **kwargs)

        table = tables.NetBoxAttachmentTable
        tab = ViewTab(
            label="Attachments",
            badge=lambda obj: models.NetBoxAttachment.objects.filter(
                content_type=ContentType.objects.get_for_model(obj),
                object_id=obj.id,
            ).count(),
            hide_if_empty=False,
        )

        def get_children(self, request, parent):
            childrens = self.child_model.objects.filter(
                content_type=ContentType.objects.get_for_model(parent),
                object_id=parent.id,
            )
            return childrens

        def get_extra_context(self, request, instance):
            data = {
                "base_template_name": base_template_name,
                "netbox_attachments": self.child_model.objects.filter(content_type=ContentType.objects.get_for_model(instance), object_id=instance.id,)
            }
            return data

    register_model_view(model, name=name, path=path)(View)


# Generate plugin extension for all classes
try:
    # Iterate over all NetBox models
    for content_type in ContentType.objects.all():
        app_label = content_type.app_label
        model = content_type.model
        app_model_name = f"{app_label}.{model}"

        # Skip if app is not present in configuration
        if app_label not in plugin_settings.get("apps"):
            continue

        # Load prefeed display setting and model class
        display = get_display_on(app_model_name)
        model = ContentType.objects.get(
            app_label=app_label, model=model).model_class()

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
        dynamic_klass = type(klass_name,
                             (PluginTemplateExtension,),
                             {"model": app_model_name,
                              display: create_attachments_panel}
                             )

        template_extensions.append(dynamic_klass)
except OperationalError as e:
    logger = logging.getLogger('netbox.netbox-attachments')
    logger.error("Database is not ready")
    logger.debug(e)
except Exception as e:
    logger = logging.getLogger('netbox.netbox-attachments')
    logger.error("Unexpected error - netbox-attachments won't be rendered")
    logger.debug(e)
