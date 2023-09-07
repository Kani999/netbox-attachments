import django_filters
from django.db.models import Q
from extras.filters import TagFilter
from netbox.filtersets import BaseFilterSet
from utilities.filters import ContentTypeFilter

from .models import NetBoxAttachment


class NetBoxAttachmentFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )
    created = django_filters.DateTimeFilter()
    content_type = ContentTypeFilter()
    name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")
    tag = TagFilter()

    class Meta:
        model = NetBoxAttachment
        fields = ['id', 'content_type_id', 'object_id', 'name', 'description']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        name_filter = Q(name__icontains=value)
        description_filter = Q(description__icontains=value)
        return queryset.filter(name_filter | description_filter)
