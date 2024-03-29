# Generated by Django 4.1.5 on 2023-01-31 11:41

from django.db import migrations, models
import utilities.json


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_attachments', '0003_alter_netboxattachment_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='netboxattachment',
            name='size',
            field=models.PositiveBigIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='netboxattachment',
            name='custom_field_data',
            field=models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
        ),
    ]
