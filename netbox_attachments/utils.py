from pathlib import Path

from django.conf import settings

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netbox_attachments", {})

def choice_default(value, choices, default=None):
    """
    Return value only if present in choices, else return default value
    """
    if value not in choices:
        return default
    return value


def attachment_upload(instance, filename):
    """
    Return a path for uploading file attchments.
    """
    path = "netbox-attachments/"

    if instance.name != filename:
        # Rename the file to the provided name, if any. Attempt to preserve the file extension.
        extension = "".join(Path(filename).suffixes)
        filename = "".join([instance.name, extension])

    return "{}{}_{}_{}".format(
        path, instance.object_type.name, instance.object_id, filename
    )


def validate_object_type(model):
    """
    Check if model is allowed to have attachments by checking plugin settings
    """
    applied_scope = choice_default(PLUGIN_SETTINGS.get("applied_scope"), ('app', 'model', ), 'app')
    scope_filter = PLUGIN_SETTINGS.get("scope_filter", [])
    model_match = model._meta.app_label

    if applied_scope == 'app':
        return model_match in scope_filter
    elif applied_scope == 'model':
        model_match = f"{model_match}.{model._meta.model_name}"
        return model_match in scope_filter

    return False
