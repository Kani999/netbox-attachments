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


def is_custom_object_model(model):
    """
    Determines if a model is a NetBox Custom Objects dynamic model.

    Checks if the model is from the netbox_custom_objects app and inherits
    from the CustomObject base class. This excludes the plugin's metadata
    models like CustomObjectType, CustomObjectTypeField, etc.

    Args:
        model: A Django model class

    Returns:
        bool: True if this is a custom object model, False otherwise
    """
    if model._meta.app_label != 'netbox_custom_objects':
        return False

    try:
        from netbox_custom_objects.models import CustomObject
        return (
            issubclass(model, CustomObject) and
            model is not CustomObject and
            not model._meta.abstract
        )
    except (ImportError, AttributeError):
        return False


def validate_object_type(model):
    """
    Determines if a Django model is permitted to have attachments.

    This function uses a unified filtering approach for both standard models and custom objects.
    It checks the model against the plugin's scope_filter configuration.

    For custom objects, the function uses CustomObjectType names in the format:
    'netbox_custom_objects.{CustomObjectType.name}' (e.g., 'netbox_custom_objects.attachment')

    When applied_scope='model', the function supports mixed mode filtering:
    - App label entries (e.g., 'dcim') enable ALL models from that app
    - Specific model entries (e.g., 'dcim.device') enable only that model

    Args:
        model: A Django model class or instance with a _meta attribute that contains
               'app_label' and 'model_name'.

    Returns:
        bool: True if the model is allowed to have attachments; False otherwise.
    """
    applied_scope = choice_default(
        PLUGIN_SETTINGS.get("applied_scope"),
        ("app", "model"),
        "app"
    )
    scope_filter = PLUGIN_SETTINGS.get("scope_filter")
    if scope_filter is None or not isinstance(scope_filter, (list, tuple, set)):
        scope_filter = []

    # Get the model identifier
    # For custom objects, use CustomObjectType name; for standard models, use model_name
    if is_custom_object_model(model):
        try:
            from netbox_custom_objects.models import CustomObjectType
            cot = CustomObjectType.objects.get(id=model.custom_object_type_id)
            model_identifier = f"{model._meta.app_label}.{cot.name}"
        except (ImportError, AttributeError, CustomObjectType.DoesNotExist):
            return False
    else:
        model_identifier = f"{model._meta.app_label}.{model._meta.model_name}"

    app_label = model._meta.app_label

    if applied_scope == "app":
        # App mode: only check app_label
        return app_label in scope_filter

    elif applied_scope == "model":
        # Model mode: check BOTH app_label (whole app) AND model_identifier (specific model)
        # This supports mixed mode: ['dcim', 'ipam.ipaddress', 'netbox_custom_objects.attachment']
        return app_label in scope_filter or model_identifier in scope_filter

    return False
