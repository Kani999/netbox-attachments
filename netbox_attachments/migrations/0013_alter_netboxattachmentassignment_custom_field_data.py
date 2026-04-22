import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_attachments', '0012_netboxattachment_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='netboxattachmentassignment',
            name='custom_field_data',
            field=models.JSONField(
                blank=True,
                default=dict,
                encoder=utilities.json.CustomFieldJSONEncoder,
            ),
        ),
    ]
