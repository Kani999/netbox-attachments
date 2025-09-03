from core.models.object_types import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from netbox.api.fields import ContentTypeField
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from utilities.api import get_serializer_for_model

from netbox_attachments.models import NetBoxAttachment


class NetBoxAttachmentSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_attachments-api:netboxattachment-detail"
    )
    object_type = ContentTypeField(queryset=ObjectType.objects.all())
    parent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NetBoxAttachment
        fields = [
            "id",
            "url",
            "display",
            "object_type",
            "object_id",
            "parent",
            "name",
            "description",
            "file",
            "created",
            "last_updated",
            "comments",
        ]
        brief_fields = ("id", "url", "display", "name", "description", "file")

    def validate(self, data):
        # Validate that the parent object exists
        try:
            if "object_type" in data and "object_id" in data:
                data["object_type"].get_object_for_this_type(id=data["object_id"])
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "Invalid parent object: {} ID {}".format(
                    data["object_type"], data["object_id"]
                )
            )

        # Enforce model validation and capture any upstream mutations
        validated_data = super().validate(data)

        return validated_data

    # @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    def get_parent(self, obj):
        # Check for required fields first to avoid unnecessary DB lookups
        if not (
            hasattr(obj, "object_type_id")
            and obj.object_type_id
            and hasattr(obj, "object_id")
            and obj.object_id
        ):
            return None

        # Only wrap the parent dereference in try/except to let other errors bubble
        try:
            parent = obj.parent
        except ObjectDoesNotExist:
            # Handle case where parent object doesn't exist
            return None

        if parent is None:
            return None

        # Get serializer for the parent's class, not the instance
        serializer = get_serializer_for_model(parent.__class__)
        return serializer(
            parent,
            nested=True,
            context=self.context,
        ).data
