import os
from pathlib import Path

from django.conf import settings

ATTACHMENT_PATH = "netbox-attachments/"
ATTACHMENT_MEDIA_ROOT = os.path.join(settings.MEDIA_ROOT, ATTACHMENT_PATH)


def attachment_upload(instance, filename):
    """
    Return a path for uploading file attchments.
    """

    if instance.name != filename:
        # Rename the file to the provided name, if any. Attempt to preserve the file extension.
        extension = "".join(Path(filename).suffixes)
        filename = "".join([instance.name, extension])

    return "{}{}_{}_{}".format(
        ATTACHMENT_PATH, instance.object_type.name, instance.object_id, filename
    )
