from core.models.object_types import ObjectType
from django import forms
from django.utils.translation import gettext as _
from netbox.forms import (
    NetBoxModelBulkEditForm,
    NetBoxModelFilterSetForm,
    NetBoxModelForm,
)
from utilities.forms.fields import (
    CommentField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.widgets.apiselect import APISelectMultiple

from netbox_attachments.models import NetBoxAttachment
from netbox_attachments.utils import validate_object_type


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

    def clean(self):
        cleaned_data = super().clean()
        self._validate_object_type()
        return cleaned_data

    def _validate_object_type(self):
        """Validate that the attachment's object type is permitted."""
        object_type = getattr(self.instance, "object_type", None)

        if object_type:
            model_class = object_type.model_class()
            if not validate_object_type(model_class):
                model_name = f"{object_type.app_label}.{object_type.model}"
                raise forms.ValidationError(
                    message=f"Attachments are not permitted for {model_name}",
                    code="invalid_attachment_target",
                )


class NetBoxAttachmentFilterForm(NetBoxModelFilterSetForm):
    model = NetBoxAttachment
    name = forms.CharField(required=False)
    description = forms.CharField(required=False)
    object_type_id = DynamicModelMultipleChoiceField(
        queryset=ObjectType.objects.all(),
        required=False,
        label=_("Object Type"),
        widget=APISelectMultiple(
            api_url="/api/core/object-types/",
        ),
    )
    tag = TagFilterField(model)


class NetBoxAttachmentBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(
        max_length=NetBoxAttachment._meta.get_field("name").max_length, required=False
    )
    description = forms.CharField(
        widget=forms.Textarea,
        max_length=NetBoxAttachment._meta.get_field("description").max_length,
        required=False,
    )

    model = NetBoxAttachment
    nullable_fields = ("name", "description")
