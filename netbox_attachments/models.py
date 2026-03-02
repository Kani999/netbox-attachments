import os

from core.models.object_types import ObjectType
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
    An uploaded attachment which may be linked to one or more objects.
    """

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
    description = models.CharField(verbose_name=_("description"), max_length=200, blank=True)
    comments = models.TextField(blank=True)

    objects = RestrictedQuerySet.as_manager()

    clone_fields = ()

    class Meta:
        ordering = ("name", "pk")  # name may be non-unique
        verbose_name_plural = "NetBox Attachments"
        verbose_name = "NetBox Attachment"

    def __str__(self):
        label = self.name or self.filename
        if self.pk:
            return f"#{self.pk} - {label}"
        return label

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def get_absolute_url(self):
        return reverse("plugins:netbox_attachments:netboxattachment", args=[self.pk])

    def delete(self, *args, **kwargs):
        """
        Deletes the instance and its associated file while preserving the original filename.
        """
        _name = self.file.name

        super().delete(*args, **kwargs)

        # Delete file from disk
        self.file.delete(save=False)

        # Restore the filename for any post-deletion references
        self.file.name = _name

    def save(self, *args, **kwargs):
        """
        Saves the attachment after updating file attributes.
        """
        if not self.file:
            return super().save(*args, **kwargs)

        try:
            self.size = self.file.size
        except OSError:
            self.size = None

        if not self.name:
            if self._state.adding:
                self.name = self.file.name.rsplit("/", 1)[-1]
            else:
                self.name = self.filename

        super().save(*args, **kwargs)

    def to_objectchange(self, action):
        objectchange = super().to_objectchange(action)
        return objectchange


class NetBoxAttachmentAssignment(NetBoxModel):
    """
    A link between a NetBoxAttachment and a NetBox object.
    """

    attachment = models.ForeignKey(
        to=NetBoxAttachment,
        on_delete=models.CASCADE,
        related_name="attachment_assignments",
    )
    object_type = models.ForeignKey(
        to=ObjectType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveBigIntegerField()

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("attachment", "object_type", "object_id")
        verbose_name_plural = "NetBox Attachment Assignments"
        verbose_name = "NetBox Attachment Assignment"
        constraints = [
            models.UniqueConstraint(
                fields=("attachment", "object_type", "object_id"),
                name="unique_attachment_assignment",
            )
        ]
        indexes = [
            models.Index(fields=["object_type", "object_id"], name="nba_assign_obj_type_id_idx"),
        ]

    def __str__(self):
        return f"Assignment #{self.pk}"

    def get_display(self):
        """Rich display — only call when parent is prefetched or single-object context."""
        parent = self.parent
        if parent:
            return f"{self.attachment} → {parent}"
        return f"{self.attachment} → {self.object_type} #{self.object_id}"

    @property
    def parent(self):
        if not (self.object_type_id and self.object_id):
            return None

        if self.object_type.model_class() is None:
            # Model was probably deleted or uninstalled
            return None

        try:
            return self.object_type.get_object_for_this_type(id=self.object_id)
        except ObjectDoesNotExist:
            return None

    def get_absolute_url(self):
        return self.attachment.get_absolute_url()


@receiver(pre_delete)
def pre_delete_receiver(sender, instance, **kwargs):
    """
    When a NetBox object is deleted, remove all of its attachment assignments.
    Attachments themselves are not deleted; they persist until explicitly removed.
    """
    # Skip if the sender is one of our own models (avoid recursion)
    if sender in (NetBoxAttachment, NetBoxAttachmentAssignment):
        return
    # Skip high-frequency Django internal models
    if sender._meta.app_label in ("sessions", "admin", "contenttypes", "auth", "taggit", "users"):
        return

    try:
        object_type = ObjectType.objects.get_for_model(instance)
    except ObjectType.DoesNotExist:
        return

    try:
        # Delete the assignments for this object; attachments are left intact
        # (QuerySet.delete() is a no-op on an empty queryset — no need for .exists() guard)
        NetBoxAttachmentAssignment.objects.filter(object_type_id=object_type.id, object_id=instance.pk).delete()
    except (TypeError, ValueError):
        # instance.pk is not an integer type — no assignments can exist for it
        return
