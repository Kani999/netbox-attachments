from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from extras.plugins import PluginTemplateExtension

from .models import NetBoxAttachment

plugin_settings = settings.PLUGINS_CONFIG.get('netbox_attachments', {})
template_extensions = []


def right_page(self):
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


# Generate plugin extension for all classes
for content_type in ContentType.objects.all():
    app_label = content_type.app_label
    model = content_type.model

    if app_label in plugin_settings.get("apps"):
        klass_name = f"{app_label}_{model}_plugin_template_extension"
        dynamic_klass = type(klass_name,
                             (PluginTemplateExtension, ),
                             {"model": f"{app_label}.{model}",
                                 "right_page": right_page})

        template_extensions.append(dynamic_klass)
