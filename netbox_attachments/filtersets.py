import django_filters
from django.db.models import Q
from extras.filters import TagFilter
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filters import ContentTypeFilter

from netbox_attachments.models import NetBoxAttachment


class NetBoxAttachmentFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    created = django_filters.DateTimeFilter()
    object_type = ContentTypeFilter()
    name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")
    tag = TagFilter()

    class Meta:
        model = NetBoxAttachment
        fields = ["id", "object_type_id", "object_id", "name", "description"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        filters = Q(name__icontains=value) | Q(description__icontains=value)
        return queryset.filter(filters)
