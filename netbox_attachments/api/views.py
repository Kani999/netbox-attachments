from netbox.api.metadata import ContentTypeMetadata
from netbox.api.viewsets import NetBoxModelViewSet

from netbox_attachments import filtersets, models
from netbox_attachments.api.serializers import NetBoxAttachmentSerializer


class NetBoxAttachmentViewSet(NetBoxModelViewSet):
    metadata_class = ContentTypeMetadata
    queryset = models.NetBoxAttachment.objects.all()
    serializer_class = NetBoxAttachmentSerializer
    filterset_class = filtersets.NetBoxAttachmentFilterSet
