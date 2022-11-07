from netbox.api.metadata import ContentTypeMetadata
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from .serializers import NetBoxAttachmentSerializer


class NetBoxAttachmentViewSet(NetBoxModelViewSet):
    metadata_class = ContentTypeMetadata
    queryset = models.NetBoxAttachment.objects.all()
    serializer_class = NetBoxAttachmentSerializer
    filterset_class = filtersets.NetBoxAttachmentFilterSet
