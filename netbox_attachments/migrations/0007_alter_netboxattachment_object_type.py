# Generated by Django 5.0.6 on 2024-07-16 12:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_gfk_indexes"),
        ("netbox_attachments", "0006_rename_content_type_netboxattachment_object_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="netboxattachment",
            name="object_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="core.objecttype"
            ),
        ),
    ]
