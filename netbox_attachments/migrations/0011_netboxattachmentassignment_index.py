from django.db import migrations, models


class Migration(migrations.Migration):
    """Add composite index on (object_type, object_id) for NetBoxAttachmentAssignment."""

    dependencies = [
        ("netbox_attachments", "0010_remove_attachment_fk_fields"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="netboxattachmentassignment",
            index=models.Index(
                fields=["object_type", "object_id"],
                name="nba_assign_obj_type_id_idx",
            ),
        ),
    ]
