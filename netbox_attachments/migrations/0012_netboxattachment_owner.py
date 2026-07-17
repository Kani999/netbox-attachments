import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_attachments", "0011_netboxattachmentassignment_index"),
        ("users", "0015_owner"),
    ]

    operations = [
        migrations.AddField(
            model_name="netboxattachment",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="users.owner",
            ),
        ),
    ]
