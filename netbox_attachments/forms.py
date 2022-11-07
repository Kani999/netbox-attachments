from netbox.forms import NetBoxModelForm

from .models import NetBoxAttachment


class NetBoxAttachmentForm(NetBoxModelForm):

    class Meta:
        model = NetBoxAttachment
        fields = [
            'name', 'file',
        ]
