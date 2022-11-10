import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import NetBoxAttachment

ATTACHMENT_LINK = """
<a href="{% url 'plugins:netbox_attachments:netboxattachment' pk=record.pk %}">
    {{ record }}
</a> (<a href="{{record.file.url}}" target="_blank">Download</a>)
"""
FILE_SIZE = "{{ record.size|filesizeformat }}"


class NetBoxAttachmentTable(NetBoxTable):
    name = tables.TemplateColumn(template_code=ATTACHMENT_LINK)
    content_type = columns.ContentTypeColumn()
    parent = tables.RelatedLinkColumn()
    tags = columns.TagColumn()
    file = tables.FileColumn()
    size = tables.TemplateColumn(template_code=FILE_SIZE)

    class Meta(NetBoxTable.Meta):
        model = NetBoxAttachment
        fields = ('pk', 'id', 'name', 'parent', 'content_type', 'object_id', 'file',
                  'size', 'comments', 'actions', 'created', 'last_updated', 'tags')
        default_columns = ('id', 'name', 'parent',
                           'content_type', 'object_id', 'tags')
