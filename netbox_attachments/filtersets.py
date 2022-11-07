import django_filters
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

    class Meta:
        model = NetBoxAttachment
        fields = ['id', 'content_type_id', 'object_id', 'name']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(name__icontains=value)
