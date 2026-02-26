import django.core.serializers.json
import django.db.models.deletion
import taggit.managers
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0134_owner"),
        ("core", "0010_gfk_indexes"),
        ("netbox_attachments", "0007_alter_netboxattachment_object_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="NetBoxAttachmentAssignment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                    ),
                ),
                ("object_id", models.PositiveBigIntegerField()),
                (
                    "attachment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachment_assignments",
                        to="netbox_attachments.netboxattachment",
                    ),
                ),
                (
                    "object_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.objecttype",
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(
                        through="extras.TaggedItem",
                        to="extras.Tag",
                        help_text="A comma-separated list of tags.",
                        verbose_name="Tags",
                    ),
                ),
            ],
            options={
                "verbose_name": "NetBox Attachment Assignment",
                "verbose_name_plural": "NetBox Attachment Assignments",
                "ordering": ("attachment", "object_type", "object_id"),
            },
        ),
        migrations.AddConstraint(
            model_name="netboxattachmentassignment",
            constraint=models.UniqueConstraint(
                fields=("attachment", "object_type", "object_id"),
                name="unique_attachment_assignment",
            ),
        ),
    ]
