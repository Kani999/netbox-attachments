from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from extras.plugins import PluginTemplateExtension
from django.apps import apps
from .models import NetBoxAttachment


plugin_settings = settings.PLUGINS_CONFIG.get('netbox_attachments', {})
template_extensions = []

def right_page(self):
    obj = self.context['object']
    return self.render(
        'netbox_attachments/netbox_attachment_panel.html',
        extra_context={
            'files': NetBoxAttachment.objects.filter(content_type=ContentType.objects.get(app_label=self.model.split(".")[0], model=self.model.split(".")[1]).id, object_id=obj.id),
        }
    )


# Generate plugin extension for all classes
for app_label, classes in apps.all_models.items():
    if app_label in plugin_settings.get("apps"):
        for model_name, model_class in classes.items():
            name = model_name + "_plugin_template_extension"
            dynamic_klass = type(name,
                                 (PluginTemplateExtension, ),
                                 {"model": f"{app_label}.{model_name}",
                                     "right_page": right_page})

            template_extensions.append(dynamic_klass)
