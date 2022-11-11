import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.utils import OperationalError
from extras.plugins import PluginTemplateExtension

from .models import NetBoxAttachment

plugin_settings = settings.PLUGINS_CONFIG.get('netbox_attachments', {})
template_extensions = []


def attachments_panel(self):
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
    """Get prefered display setting (left_page, right_page, full_width_page) for attachment panel

    Args:
        app_model_name (str): <app_label>.<model> = (dcim.device, ipam.vlan, ...)

    Returns:
        str: Configured display setting or default
    """
    # set default
    display_on = plugin_settings.get("display_default", "right_page")

    # Find configured display setting or return default
    if display_setting := plugin_settings.get('display_setting'):
        display_on = display_setting.get(app_model_name, display_on)

    return display_on


# Generate plugin extension for all classes
try:
    for content_type in ContentType.objects.all():
        app_label = content_type.app_label
        model = content_type.model
        app_model_name = f"{app_label}.{model}"

        if app_label in plugin_settings.get("apps"):
            klass_name = f"{app_label}_{model}_plugin_template_extension"

            dynamic_klass = type(klass_name,
                                 (PluginTemplateExtension,),
                                 {"model": app_model_name,
                                  get_display_on(app_model_name): attachments_panel}
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
