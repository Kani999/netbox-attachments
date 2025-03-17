from pathlib import Path

from django.conf import settings

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netbox_attachments", {})


def choice_default(value, choices, default=None):
    """
    Return the given value if it is among the allowed choices, or return the default value.

    Checks if the provided value exists in the collection of choices. If found, the value is returned;
    otherwise, the specified default (or None if not provided) is returned.
    """

    # Return value only if present in choices, else return default value
    if value not in choices:
        return default
    return value


def attachment_upload(instance, filename):
    """
    Generate a file upload path for an attachment.

    Constructs an upload path using a fixed directory prefix ("netbox-attachments/"), the
    instance's object type name, object ID, and a filename. If the provided filename differs
    from the instance's name, the filename is updated to match the instance's name while preserving
    its original file extension(s).

    Args:
        instance: A model instance with attributes 'name', 'object_type', and 'object_id'.
        filename: The original filename; its extension(s) are preserved if a rename is applied.

    Returns:
        A string representing the formatted file upload path.
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
    Determines if a Django model is permitted to have attachments.

    This function checks the provided model against plugin settings to verify whether it
    is allowed to have attachments. Depending on the 'applied_scope' setting—either 'app' or
    'model'—the function verifies that either the model's app label or the combined
    "app_label.model_name" is present in the scope filter. The default scope 'app' is used
    if the configuration is missing or invalid.

    Args:
        model: A Django model class or instance with a _meta attribute that contains
               'app_label' and 'model_name'.

    Returns:
        bool: True if the model is allowed to have attachments; False otherwise.
    """
    # Check if model is allowed to have attachments by checking plugin settings

    applied_scope = choice_default(
        PLUGIN_SETTINGS.get("applied_scope"),
        (
            "app",
            "model",
        ),
        "app",
    )
    scope_filter = PLUGIN_SETTINGS.get("scope_filter", [])
    model_match = model._meta.app_label

    if applied_scope == "app":
        return model_match in scope_filter
    elif applied_scope == "model":
        model_match = f"{model_match}.{model._meta.model_name}"
        return model_match in scope_filter

    return False
