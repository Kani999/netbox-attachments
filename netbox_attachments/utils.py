from pathlib import Path


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
