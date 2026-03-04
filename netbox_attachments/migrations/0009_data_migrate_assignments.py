"""
Data migration: copy existing (object_type_id, object_id) pairs from each
NetBoxAttachment into the new NetBoxAttachmentAssignment table.
"""

from django.db import migrations


def copy_assignments_forward(apps, schema_editor):
    NetBoxAttachment = apps.get_model("netbox_attachments", "NetBoxAttachment")
    NetBoxAttachmentAssignment = apps.get_model("netbox_attachments", "NetBoxAttachmentAssignment")

    assignments = []
    for attachment in NetBoxAttachment.objects.all():
        if attachment.object_type_id and attachment.object_id:
            assignments.append(
                NetBoxAttachmentAssignment(
                    attachment_id=attachment.pk,
                    object_type_id=attachment.object_type_id,
                    object_id=attachment.object_id,
                )
            )

    if assignments:
        NetBoxAttachmentAssignment.objects.bulk_create(assignments, ignore_conflicts=True)


def copy_assignments_backward(apps, schema_editor):
    """Restore object_type_id / object_id from the first assignment (best-effort)."""
    NetBoxAttachment = apps.get_model("netbox_attachments", "NetBoxAttachment")
    NetBoxAttachmentAssignment = apps.get_model("netbox_attachments", "NetBoxAttachmentAssignment")

    for attachment in NetBoxAttachment.objects.all():
        assignment = NetBoxAttachmentAssignment.objects.filter(attachment_id=attachment.pk).order_by("pk").first()
        if assignment:
            attachment.object_type_id = assignment.object_type_id
            attachment.object_id = assignment.object_id
            attachment.save(update_fields=["object_type_id", "object_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_attachments", "0008_create_netboxattachmentassignment"),
    ]

    operations = [
        migrations.RunPython(
            copy_assignments_forward,
            reverse_code=copy_assignments_backward,
        ),
    ]
