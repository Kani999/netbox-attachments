from netbox.search import SearchIndex, register_search

from netbox_attachments.models import NetBoxAttachment


@register_search
class NetBoxAttachmentIndex(SearchIndex):
    model = NetBoxAttachment
    fields = (
        ("name", 100),
        ("filename", 110),
        ("description", 500),
        ("comments", 5000),
    )
    display_attrs = ("description",)
