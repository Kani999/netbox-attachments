import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from netbox_attachments.models import NetBoxAttachment, NetBoxAttachmentAssignment

ATTACHMENT_LINK = """
<a href="{% url 'plugins:netbox_attachments:netboxattachment' pk=record.pk %}">
    {{ record }}
</a>
"""
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

UNLINK_BUTTON = """
<a href="{% url 'plugins:netbox_attachments:netboxattachmentassignment_delete' pk=record.pk %}?return_url={{ request.path|urlencode }}"
   class="btn btn-sm btn-danger"
   title="Unlink">
    <i class="mdi mdi-link-off"></i>
</a>
"""


def get_missing_parent_row_class(record):
    assignments = record.attachment_assignments.all()
    if not assignments.exists():
        return "danger"
    return ""


class NetBoxAttachmentTable(NetBoxTable):
    name = tables.TemplateColumn(template_code=ATTACHMENT_LINK)
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
    object_type = columns.ContentTypeColumn(verbose_name="Object Type")
    parent = tables.TemplateColumn(
        template_code=ASSIGNMENT_PARENT_COLUMN,
        verbose_name="Object",
        orderable=False,
    )
    actions = columns.ActionsColumn(actions=(), extra_buttons=UNLINK_BUTTON)

    class Meta(NetBoxTable.Meta):
        model = NetBoxAttachmentAssignment
        fields = (
            "pk",
            "object_type",
            "parent",
            "created",
            "actions",
        )
        default_columns = (
            "object_type",
            "parent",
            "created",
            "actions",
        )
