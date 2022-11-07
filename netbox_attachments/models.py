from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from netbox.models import NetBoxModel
from utilities.querysets import RestrictedQuerySet

from .utils import attachment_upload


class NetBoxAttachment(NetBoxModel):
    """
    An uploaded attachment which is associated with an object.
    """
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveBigIntegerField()
    parent = GenericForeignKey(
        ct_field='content_type',
        fk_field='object_id'
    )
    file = models.FileField(
        upload_to=attachment_upload,
    )
    name = models.CharField(
        max_length=50,
        blank=True
    )

    objects = RestrictedQuerySet.as_manager()

    clone_fields = ('content_type', 'object_id')

    class Meta:
        ordering = ('name', 'pk')  # name may be non-unique

    def __str__(self):
        if self.name:
            return self.name
        filename = self.file.name.rsplit('/', 1)[-1]
        return filename.split('_', 2)[2]

    def delete(self, *args, **kwargs):

        _name = self.file.name

        super().delete(*args, **kwargs)

        # Delete file from disk
        self.file.delete(save=False)

        # Deleting the file erases its name. We restore the image's filename here in case we still need to reference it
        # before the request finishes. (For example, to display a message indicating the ImageAttachment was deleted.)
        self.file.name = _name

    @property
    def size(self):
        """
        Wrapper around `file.size` to suppress an OSError in case the file is inaccessible. Also opportunistically
        catch other exceptions that we know other storage back-ends to throw.
        """
        expected_exceptions = [OSError]

        try:
            from botocore.exceptions import ClientError
            expected_exceptions.append(ClientError)
        except ImportError:
            pass

        try:
            return self.file.size
        except tuple(expected_exceptions):
            return None

    def to_objectchange(self, action):
        objectchange = super().to_objectchange(action)
        objectchange.related_object = self.parent
        return objectchange
