# Generated by Django 4.2.4 on 2023-09-07 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_attachments', '0004_netboxattachment_size_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='netboxattachment',
            name='description',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
