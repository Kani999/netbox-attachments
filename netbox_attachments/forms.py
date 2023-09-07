from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.widgets.apiselect import APISelectMultiple
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField, CommentField

from .models import NetBoxAttachment


class NetBoxAttachmentForm(NetBoxModelForm):
    comments = CommentField(label="Comment")

    class Meta:
        model = NetBoxAttachment
        fields = [
            'name', 'description', 'file', 'comments', 'tags',
        ]


class NetBoxAttachmentFilterForm(NetBoxModelFilterSetForm):
    model = NetBoxAttachment
    name = forms.CharField(required=False)
    description = forms.CharField(required=False)
    content_type_id = DynamicModelMultipleChoiceField(
        queryset=ContentType.objects.all(),
        required=False,
        label=_('Object Type'),
        widget=APISelectMultiple(
            api_url='/api/extras/content-types/',
        )
    )
    tag = TagFilterField(model)
