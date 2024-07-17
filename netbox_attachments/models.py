import numbers
import os

from core.models.contenttypes import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel
from utilities.querysets import RestrictedQuerySet

from netbox_attachments.utils import attachment_upload


class NetBoxAttachment(NetBoxModel):
    """
    An uploaded attachment which is associated with an object.
    """

    object_type = models.ForeignKey(to=ObjectType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    file = models.FileField(
        upload_to=attachment_upload,
    )
    size = models.PositiveBigIntegerField(
        editable=False,
        null=True,
        blank=True,
        help_text="Size of the file in bytes",
    )
    name = models.CharField(max_length=254, blank=True)
    description = models.CharField(
        verbose_name=_("description"), max_length=200, blank=True
    )
    comments = models.TextField(blank=True)

    objects = RestrictedQuerySet.as_manager()

    clone_fields = ("object_type", "object_id")

    class Meta:
        ordering = ("name", "pk")  # name may be non-unique
        verbose_name_plural = "NetBox Attachments"
        verbose_name = "NetBox Attachment"

    def __str__(self):
        if self.name:
            return self.name

        return self.filename

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def parent(self):
        if self.object_type.model_class() is None:
            # Model for the content type does not exists
            # Model was probably deleted or uninstalled -> parent object cannot be found
            return None
        try:
            return self.object_type.get_object_for_this_type(id=self.object_id)
        except ObjectDoesNotExist:
            # Object for the content type Model does not exists
            return None

    def get_absolute_url(self):
        return reverse("plugins:netbox_attachments:netboxattachment", args=[self.pk])

    def delete(self, *args, **kwargs):
        _name = self.file.name

        super().delete(*args, **kwargs)

        # Delete file from disk
        self.file.delete(save=False)

        # Deleting the file erases its name. We restore the image's filename here in case we still need to reference it
        # before the request finishes. (For example, to display a message indicating the ImageAttachment was deleted.)
        self.file.name = _name

    def save(self, *args, **kwargs):
        self.size = self.file.size

        if not self.file:
            return super().save(*args, **kwargs)

        if not self.name:
            if self._state.adding:
                self.name = self.file.name.rsplit("/", 1)[-1]
            else:
                self.name = self.filename.split("_", 2)[2]

        super().save(*args, **kwargs)

    def to_objectchange(self, action):
        objectchange = super().to_objectchange(action)
        objectchange.related_object = self.parent
        return objectchange

    @receiver(pre_delete)
    def pre_delete_receiver(sender, instance, **kwargs):
        # code that delete the related objects
        # As you don't have generic relation you should manually
        # find related actitities

        # Workaround: only run signals on Models where PK is Integral
        # https://github.com/Kani999/netbox-attachments/issues/44
        if isinstance(instance.pk, numbers.Integral):
            object_type = ObjectType.objects.get_for_model(instance)
            attachments = NetBoxAttachment.objects.filter(
                object_type_id=object_type.id, object_id=instance.pk
            )
            if attachments:
                attachments.delete()
