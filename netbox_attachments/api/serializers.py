from core.models.object_types import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from netbox.api.fields import ContentTypeField
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from utilities.api import get_serializer_for_model

from netbox_attachments.models import NetBoxAttachment, NetBoxAttachmentAssignment


class NetBoxAttachmentAssignmentSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_attachments-api:netboxattachmentassignment-detail"
    )
    object_type = ContentTypeField(queryset=ObjectType.objects.all())
    parent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NetBoxAttachmentAssignment
        fields = [
            "id",
            "url",
            "display",
            "attachment",
            "object_type",
            "object_id",
            "parent",
            "created",
            "last_updated",
        ]
        brief_fields = ("id", "url", "display", "object_type", "object_id")

    def validate(self, data):
        # Validate that the parent object exists.
        # Fall back to instance values so PATCH requests that only supply one
        # of the two fields are still validated against the full pair.
        object_type = data.get("object_type", getattr(self.instance, "object_type", None))
        object_id = data.get("object_id", getattr(self.instance, "object_id", None))
        if object_type is not None and object_id is not None:
            try:
                object_type.get_object_for_this_type(id=object_id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    "Invalid parent object: {} ID {}".format(object_type, object_id)
                )
        return super().validate(data)

    def get_parent(self, obj):
        try:
            parent = obj.parent
        except ObjectDoesNotExist:
            return None

        if parent is None:
            return None

        serializer = get_serializer_for_model(parent.__class__)
        return serializer(parent, nested=True, context=self.context).data


class NetBoxAttachmentSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_attachments-api:netboxattachment-detail")
    assignments = NetBoxAttachmentAssignmentSerializer(
        source="attachment_assignments",
        many=True,
        read_only=True,
    )

    class Meta:
        model = NetBoxAttachment
        fields = [
            "id",
            "url",
            "display",
            "name",
            "description",
            "file",
            "size",
            "assignments",
            "created",
            "last_updated",
            "comments",
            "tags",
        ]
        brief_fields = ("id", "url", "display", "name", "description", "file")
