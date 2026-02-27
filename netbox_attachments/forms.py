import logging

from core.models.object_types import ObjectType
from django import forms
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)
from netbox.forms import (
    NetBoxModelBulkEditForm,
    NetBoxModelFilterSetForm,
    NetBoxModelForm,
)
from utilities.forms.fields import (
    CommentField,
    ContentTypeChoiceField,
    DynamicModelChoiceField,
    TagFilterField,
)
from utilities.forms.utils import get_field_value
from utilities.forms.widgets import HTMXSelect
from utilities.forms.widgets.apiselect import APISelect

from netbox_attachments.models import NetBoxAttachment, NetBoxAttachmentAssignment
from netbox_attachments.utils import get_enabled_object_type_queryset


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

    def save(self, commit=True):
        """
        After saving the attachment, create an assignment if pending context is set.
        The view's alter_object() sets _pending_object_type_id and _pending_object_id
        on the instance to pass context into this save() method.
        """
        pending_type_id = getattr(self.instance, "_pending_object_type_id", None)
        pending_obj_id = getattr(self.instance, "_pending_object_id", None)

        obj = super().save(commit=commit)

        if pending_type_id and pending_obj_id and commit:
            from core.models.object_types import ObjectType

            from netbox_attachments.models import NetBoxAttachmentAssignment

            try:
                object_type = ObjectType.objects.get(pk=int(pending_type_id))
                NetBoxAttachmentAssignment.objects.get_or_create(
                    attachment=obj,
                    object_type=object_type,
                    object_id=int(pending_obj_id),
                )
            except (ObjectType.DoesNotExist, ValueError) as e:
                logger.warning(
                    "Failed to create attachment assignment: object_type_id=%s object_id=%s: %s",
                    pending_type_id, pending_obj_id, e,
                )

        return obj


class NetBoxAttachmentLinkForm(NetBoxModelForm):
    """Form for linking an existing attachment to a NetBox object."""

    attachment = DynamicModelChoiceField(
        queryset=NetBoxAttachment.objects.all(),
        label=_("Attachment"),
        widget=APISelect(
            api_url="/api/plugins/netbox-attachments/netbox-attachments/",
        ),
    )
    object_type = ContentTypeChoiceField(
        queryset=ObjectType.objects.all(),
        required=False,
        label=_("Object Type"),
        widget=HTMXSelect(),
    )
    object = DynamicModelChoiceField(
        queryset=ObjectType.objects.none(),  # placeholder; updated in __init__
        required=False,
        disabled=True,
        label=_("Object"),
    )

    class Meta:
        model = NetBoxAttachmentAssignment
        fields = ["attachment"]  # object_type / object handled manually

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.object_type_id:
            # Forward flow: object already resolved — hide picker fields
            del self.fields["object_type"]
            del self.fields["object"]
        else:
            # Restrict choices to models enabled in the plugin config
            self.fields["object_type"].queryset = get_enabled_object_type_queryset()
            if object_type_id := get_field_value(self, "object_type"):
                # Reverse flow after HTMX reload: enable object picker for chosen type
                try:
                    obj_type = ObjectType.objects.get(pk=object_type_id)
                    model = obj_type.model_class()
                    self.fields["object"].queryset = model.objects.all()
                    self.fields["object"].model = model  # update field's model ref for selector
                    self.fields["object"].selector = True  # now safe: model is the real target
                    self.fields["object"].widget.attrs["selector"] = (
                        model._meta.label_lower
                    )  # bake into widget attrs for template
                    self.fields["object"].disabled = False
                    self.fields["object"].label = _(model._meta.verbose_name.title())
                except ObjectType.DoesNotExist:
                    pass  # Type not found; object picker stays disabled
                except (AttributeError, TypeError):
                    pass  # model_class() returned None or model has no manager

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data  # safe: populated by Django before clean() is called
        attachment = cleaned_data.get("attachment")

        object_type = getattr(self.instance, "object_type", None)
        object_id = getattr(self.instance, "object_id", None)

        # Reverse flow: resolve from form fields
        if not object_type:
            object_type = cleaned_data.get("object_type")
            obj = cleaned_data.get("object")
            if not object_type:
                self.add_error("object_type", _("Object type is required."))
            if not obj:
                self.add_error("object", _("Object is required."))
            if object_type and obj:
                self.instance.object_type = object_type
                self.instance.object_id = obj.pk
                object_id = obj.pk

        # Duplicate-assignment check
        if attachment and object_type and object_id:
            if NetBoxAttachmentAssignment.objects.filter(
                attachment=attachment,
                object_type=object_type,
                object_id=object_id,
            ).exists():
                raise forms.ValidationError(_("This attachment is already linked to this object."))

        return cleaned_data


class NetBoxAttachmentFilterForm(NetBoxModelFilterSetForm):
    model = NetBoxAttachment
    name = forms.CharField(required=False)
    description = forms.CharField(required=False)
    object_type_id = DynamicModelChoiceField(
        queryset=ObjectType.objects.all(),
        required=False,
        label=_("Object Type"),
        widget=APISelect(
            api_url="/api/core/object-types/",
        ),
    )
    has_assignments = forms.BooleanField(
        required=False,
        label=_("Has Assignments"),
        widget=forms.Select(
            choices=[
                ("", "---------"),
                ("true", _("Yes")),
                ("false", _("No")),
            ]
        ),
    )
    has_broken_assignments = forms.BooleanField(
        required=False,
        label=_("Has Broken Assignments"),
        widget=forms.Select(
            choices=[
                ("", "---------"),
                ("true", _("Yes")),
                ("false", _("No")),
            ]
        ),
    )
    tag = TagFilterField(model)


class NetBoxAttachmentBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(max_length=NetBoxAttachment._meta.get_field("name").max_length, required=False)
    description = forms.CharField(
        widget=forms.Textarea,
        max_length=NetBoxAttachment._meta.get_field("description").max_length,
        required=False,
    )

    model = NetBoxAttachment
    nullable_fields = ("name", "description")
