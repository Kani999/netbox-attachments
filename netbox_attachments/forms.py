from core.models.contenttypes import ObjectType
from django import forms
from django.utils.translation import gettext as _
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import (
    CommentField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.widgets.apiselect import APISelectMultiple

from netbox_attachments.models import NetBoxAttachment


class NetBoxAttachmentForm(NetBoxModelForm):
    comments = CommentField(label="Comment")

    class Meta:
        model = NetBoxAttachment
        fields = [
            "name",
            "description",
            "file",
            "comments",
            "tags",
        ]


class NetBoxAttachmentFilterForm(NetBoxModelFilterSetForm):
    model = NetBoxAttachment
    name = forms.CharField(required=False)
    description = forms.CharField(required=False)
    object_type_id = DynamicModelMultipleChoiceField(
        queryset=ObjectType.objects.all(),
        required=False,
        label=_("Object Type"),
        widget=APISelectMultiple(
            api_url="/api/extras/object-types/",
        ),
    )
    tag = TagFilterField(model)
