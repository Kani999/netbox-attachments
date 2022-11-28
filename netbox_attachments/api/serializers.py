from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_serializer_method
from netbox.api.fields import ContentTypeField
from netbox.api.serializers import NetBoxModelSerializer
from netbox.constants import NESTED_SERIALIZER_PREFIX
from rest_framework import serializers
from utilities.api import get_serializer_for_model

from ..models import NetBoxAttachment


class NetBoxAttachmentSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_attachments-api:netboxattachment-detail')
    content_type = ContentTypeField(
        queryset=ContentType.objects.all()
    )
    parent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NetBoxAttachment
        fields = [
            'id', 'url', 'display', 'content_type', 'object_id', 'parent', 'name', 'file', 'created', 'last_updated', 'comments',
        ]

    def validate(self, data):
        # Validate that the parent object exists
        try:
            if 'content_type' in data and 'object_id' in data:
                data['content_type'].get_object_for_this_type(
                    id=data['object_id'])
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "Invalid parent object: {} ID {}".format(
                    data['content_type'], data['object_id'])
            )

        # Enforce model validation
        super().validate(data)

        return data

    @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    def get_parent(self, obj):
        serializer = get_serializer_for_model(
            obj.parent, prefix=NESTED_SERIALIZER_PREFIX)
        return serializer(obj.parent, context={'request': self.context['request']}).data
