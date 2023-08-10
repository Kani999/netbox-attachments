import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import NetBoxAttachment

ATTACHMENT_LINK = """
<a href="{% url 'plugins:netbox_attachments:netboxattachment' pk=record.pk %}">
    {{ record }}
</a>
"""
FILE_SIZE = "{{ record.size|filesizeformat }}"
DOWNLOAD_BUTTON = """
<a href="{{record.file.url}}" target="_blank" class="btn btn-sm btn-primary download-attachment" title="Download">
  <i class="mdi mdi-download"></i>
</a>
"""


class NetBoxAttachmentTable(NetBoxTable):
    name = tables.TemplateColumn(template_code=ATTACHMENT_LINK)
    content_type = columns.ContentTypeColumn()
    parent = tables.RelatedLinkColumn()
    tags = columns.TagColumn()
    file = tables.FileColumn()
    size = tables.TemplateColumn(template_code=FILE_SIZE)
    actions = columns.ActionsColumn(extra_buttons=DOWNLOAD_BUTTON)

    class Meta(NetBoxTable.Meta):
        model = NetBoxAttachment
        fields = ('pk', 'id', 'name', 'parent', 'content_type', 'object_id', 'file',
                  'size', 'comments', 'actions', 'created', 'last_updated', 'tags')
        default_columns = ('id', 'name', 'parent',
                           'content_type', 'object_id', 'tags')
