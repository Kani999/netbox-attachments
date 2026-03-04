import logging

import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from netbox_attachments.models import NetBoxAttachment, NetBoxAttachmentAssignment

logger = logging.getLogger(__name__)

FILE_SIZE = "{{ record.size|filesizeformat }}"
DOWNLOAD_BUTTON = """
<a href="{{record.file.url}}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-primary download-attachment" title="Download">
  <i class="mdi mdi-download"></i>
</a>
{% if perms.netbox_attachments.add_netboxattachmentassignment %}
<a href="{% url 'plugins:netbox_attachments:netboxattachment_link' %}?attachment={{ record.pk }}&return_url={{ request.get_full_path|urlencode }}"
   class="btn btn-sm btn-success" title="Assign">
  <i class="mdi mdi-link-variant"></i>
</a>
{% endif %}
"""

PARENT_COLUMN = """
{% load helpers %}
{% with assignments=record.attachment_assignments.all %}
    {% if not assignments %}
        <span class="text-muted">&mdash;</span>
    {% elif assignments|length == 1 %}
        {% with a=assignments|first %}
            {% if a.parent %}
                {{ a.parent|linkify }}
            {% else %}
                <span class="text-muted">{{ a.object_type.app_label }} &gt; {{ a.object_type.model }} #{{ a.object_id }}</span>
            {% endif %}
        {% endwith %}
    {% else %}
        {% for a in assignments %}
            {% if forloop.counter <= 3 %}
                {% if a.parent %}{{ a.parent|linkify }}{% else %}<span class="text-muted">{{ a.object_type.app_label }} &gt; {{ a.object_type.model }} #{{ a.object_id }}</span>{% endif %}{% if not forloop.last and forloop.counter < 3 %}, {% endif %}
            {% endif %}
        {% endfor %}
        {% if assignments|length > 3 %}
            <span class="badge bg-secondary text-white">+{{ assignments|length|add:"-3" }} more</span>
        {% endif %}
    {% endif %}
{% endwith %}
"""

ASSIGNMENT_PARENT_COLUMN = """
{% if record.parent %}
    <a href="{{ record.parent.get_absolute_url }}">{{ record.parent }}</a>
{% else %}
    <span class="text-muted">{{ record.object_type.app_label }} &gt; {{ record.object_type.model }} #{{ record.object_id }}</span>
{% endif %}
"""


ASSIGNMENT_ATTACHMENT_LINK = """
<a href="{{ record.attachment.get_absolute_url }}">{{ record.attachment }}</a>
"""

ATTACHMENT_ASSIGNMENT_SIZE = "{{ record.attachment.size|filesizeformat }}"

OBJECT_ATTACHMENT_LINKS_COUNT = """
<a href="{{ record.attachment.get_absolute_url }}">{{ record.attachment_link_count }}</a>
"""

OBJECT_ATTACHMENT_ACTIONS = """
<a href="{{ record.attachment.file.url }}" target="_blank" rel="noopener noreferrer"
   class="btn btn-sm btn-primary" title="Download">
    <i class="mdi mdi-download"></i>
</a>
"""


def get_missing_parent_row_class(record):
    count = getattr(record, "assignment_count", None)
    if count is not None:
        return "table-danger" if count == 0 else ""
    # Fallback for views without annotation
    logger.warning(
        "assignment_count annotation missing for %r; falling back to exists() query", record
    )
    return "table-danger" if not record.attachment_assignments.exists() else ""


class NetBoxAttachmentTable(NetBoxTable):
    name = tables.Column(accessor="name", verbose_name="Name", orderable=True, linkify=True)
    parent = tables.TemplateColumn(
        template_code=PARENT_COLUMN,
        verbose_name="Assigned To",
        orderable=False,
    )
    tags = columns.TagColumn()
    file = tables.FileColumn()
    size = tables.TemplateColumn(template_code=FILE_SIZE)
    actions = columns.ActionsColumn(extra_buttons=DOWNLOAD_BUTTON)

    class Meta(NetBoxTable.Meta):
        model = NetBoxAttachment
        fields = (
            "pk",
            "id",
            "name",
            "description",
            "parent",
            "file",
            "size",
            "comments",
            "actions",
            "created",
            "last_updated",
            "tags",
        )
        default_columns = (
            "id",
            "name",
            "description",
            "parent",
            "tags",
        )
        row_attrs = {
            "class": get_missing_parent_row_class,
        }


class NetBoxAttachmentAssignmentTable(NetBoxTable):
    attachment = tables.TemplateColumn(
        template_code=ASSIGNMENT_ATTACHMENT_LINK,
        verbose_name="Attachment",
        orderable=False,
    )
    object_type = columns.ContentTypeColumn(verbose_name="Object Type")
    parent = tables.TemplateColumn(
        template_code=ASSIGNMENT_PARENT_COLUMN,
        verbose_name="Object",
        orderable=False,
    )
    description = tables.Column(accessor="attachment.description", verbose_name="Description", orderable=False)
    file = tables.FileColumn(accessor="attachment.file", verbose_name="File", orderable=False)
    size = tables.TemplateColumn(template_code=ATTACHMENT_ASSIGNMENT_SIZE, verbose_name="Size", orderable=False)
    tags = columns.TagColumn(url_name="plugins:netbox_attachments:netboxattachmentassignment_list")
    actions = columns.ActionsColumn(extra_buttons=OBJECT_ATTACHMENT_ACTIONS)

    class Meta(NetBoxTable.Meta):
        model = NetBoxAttachmentAssignment
        fields = (
            "pk",
            "id",
            "attachment",
            "object_type",
            "parent",
            "description",
            "file",
            "size",
            "tags",
            "created",
            "actions",
        )
        default_columns = (
            "id",
            "attachment",
            "object_type",
            "parent",
            "tags",
            "created",
            "actions",
        )


class NetBoxAttachmentForObjectTable(NetBoxTable):
    """Table for displaying assignments on an object's attachment tab, with per-row unlink."""

    attachment_name = tables.TemplateColumn(
        template_code=ASSIGNMENT_ATTACHMENT_LINK,
        verbose_name="Attachment",
        orderable=False,
    )
    description = tables.Column(
        accessor="attachment.description",
        verbose_name="Description",
        orderable=False,
    )
    file = tables.FileColumn(
        accessor="attachment.file",
        verbose_name="File",
        orderable=False,
    )
    size = tables.TemplateColumn(
        template_code=ATTACHMENT_ASSIGNMENT_SIZE,
        verbose_name="Size",
        orderable=False,
    )
    links = tables.TemplateColumn(
        template_code=OBJECT_ATTACHMENT_LINKS_COUNT,
        verbose_name="Links",
        orderable=False,
    )
    tags = columns.TagColumn(url_name="plugins:netbox_attachments:netboxattachmentassignment_list")
    actions = columns.ActionsColumn(extra_buttons=OBJECT_ATTACHMENT_ACTIONS)

    class Meta(NetBoxTable.Meta):
        model = NetBoxAttachmentAssignment
        fields = ("pk", "id", "attachment_name", "description", "file", "size", "links", "tags", "created", "actions")
        default_columns = ("attachment_name", "description", "size", "links", "tags", "created", "actions")
