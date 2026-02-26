import django_filters
from core.models.object_types import ObjectType
from django.db.models import Q
from extras.filters import TagFilter
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filtersets import register_filterset

from netbox_attachments.models import NetBoxAttachment, NetBoxAttachmentAssignment


@register_filterset
class NetBoxAttachmentFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    created = django_filters.DateTimeFilter()
    name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")
    tag = TagFilter()

    # Filters routed through the assignment relation
    object_type_id = django_filters.NumberFilter(
        method="filter_object_type_id",
        label="Object Type (ID)",
    )
    object_id = django_filters.NumberFilter(
        method="filter_object_id",
        label="Object ID",
    )
    has_assignments = django_filters.BooleanFilter(
        method="filter_has_assignments",
        label="Has Assignments",
    )
    has_broken_assignments = django_filters.BooleanFilter(
        method="filter_has_broken_assignments",
        label="Has Broken Assignments",
    )

    class Meta:
        model = NetBoxAttachment
        fields = ["id", "name", "description"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        filters = Q(name__icontains=value) | Q(description__icontains=value)
        return queryset.filter(filters)

    def filter_object_type_id(self, queryset, name, value):
        return queryset.filter(attachment_assignments__object_type_id=value).distinct()

    def filter_object_id(self, queryset, name, value):
        return queryset.filter(attachment_assignments__object_id=value).distinct()

    def filter_has_assignments(self, queryset, name, value):
        if value:
            return queryset.filter(attachment_assignments__isnull=False).distinct()
        else:
            return queryset.filter(attachment_assignments__isnull=True).distinct()

    def filter_has_broken_assignments(self, queryset, name, value):
        broken_ids = [ot.id for ot in ObjectType.objects.all() if ot.model_class() is None]
        if value:
            return queryset.filter(attachment_assignments__object_type_id__in=broken_ids).distinct()
        return queryset.exclude(attachment_assignments__object_type_id__in=broken_ids).distinct()


@register_filterset
class NetBoxAttachmentAssignmentFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    attachment_id = django_filters.NumberFilter(
        field_name="attachment_id",
        label="Attachment (ID)",
    )
    object_type_id = django_filters.NumberFilter(
        field_name="object_type_id",
        label="Object Type (ID)",
    )
    object_id = django_filters.NumberFilter(
        field_name="object_id",
        label="Object ID",
    )

    class Meta:
        model = NetBoxAttachmentAssignment
        fields = ["id", "attachment_id", "object_type_id", "object_id"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        return queryset.filter(Q(attachment__name__icontains=value) | Q(attachment__description__icontains=value))
