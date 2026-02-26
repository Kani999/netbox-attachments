from django.db import migrations


class Migration(migrations.Migration):
    """Remove the now-redundant object_type and object_id columns from NetBoxAttachment."""

    dependencies = [
        ("netbox_attachments", "0009_data_migrate_assignments"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="netboxattachment",
            name="object_type",
        ),
        migrations.RemoveField(
            model_name="netboxattachment",
            name="object_id",
        ),
    ]
