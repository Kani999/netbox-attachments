from netbox.search import SearchIndex, register_search
from .models import NetBoxAttachment


@register_search
class NetBoxAttachmentIndex(SearchIndex):
    model = NetBoxAttachment
    fields = (
        ('name', 100),
        ('comments', 5000),
    )
