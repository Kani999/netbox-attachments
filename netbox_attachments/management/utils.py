# -*- coding: utf-8 -*-

from django.apps import apps
from django.db import models
from netbox_attachments import NetBoxAttachmentsConfig


def get_file_fields():
    """
    Get all fields which are inherited from FileField in NetBoxAttachment plugin models
    """

    # get NetBox Attachment models
    attachment_app_config = apps.get_app_config(NetBoxAttachmentsConfig.name)
    attachment_models = attachment_app_config.get_models()
    # get fields

    fields = []

    for model in attachment_models:
        for field in model._meta.get_fields():
            if isinstance(field, models.FileField):
                fields.append(field)

    return fields
