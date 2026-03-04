from netbox.api.metadata import ContentTypeMetadata
from netbox.api.viewsets import NetBoxModelViewSet

from netbox_attachments import filtersets, models
from netbox_attachments.api.serializers import (
    NetBoxAttachmentAssignmentSerializer,
    NetBoxAttachmentSerializer,
)


class NetBoxAttachmentViewSet(NetBoxModelViewSet):
    metadata_class = ContentTypeMetadata
    queryset = models.NetBoxAttachment.objects.prefetch_related(
        "attachment_assignments",
        "attachment_assignments__object_type",
    )
    serializer_class = NetBoxAttachmentSerializer
    filterset_class = filtersets.NetBoxAttachmentFilterSet


class NetBoxAttachmentAssignmentViewSet(NetBoxModelViewSet):
    metadata_class = ContentTypeMetadata
    queryset = models.NetBoxAttachmentAssignment.objects.select_related(
        "attachment",
        "object_type",
    )
    serializer_class = NetBoxAttachmentAssignmentSerializer
    filterset_class = filtersets.NetBoxAttachmentAssignmentFilterSet
