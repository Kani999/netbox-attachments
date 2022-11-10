from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from netbox.views import generic

from . import filtersets, forms, models, tables


class NetBoxAttachmentView(generic.ObjectView):
    controls = []
    queryset = models.NetBoxAttachment.objects.all()


class NetBoxAttachmentListView(generic.ObjectListView):
    actions = ['export']
    queryset = models.NetBoxAttachment.objects.all()
    table = tables.NetBoxAttachmentTable
    filterset = filtersets.NetBoxAttachmentFilterSet
    filterset_form = forms.NetBoxAttachmentFilterForm


class NetBoxAttachmentEditView(generic.ObjectEditView):
    queryset = models.NetBoxAttachment.objects.all()
    form = forms.NetBoxAttachmentForm
    template_name = 'netbox_attachments/netbox_attachment_edit.html'
    default_return_url = 'plugins:netbox_attachments:netboxattachment_list'

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            # Assign the parent object based on URL kwargs
            content_type = get_object_or_404(
                ContentType, pk=request.GET.get('content_type'))
            instance.parent = get_object_or_404(
                content_type.model_class(), pk=request.GET.get('object_id'))
        return instance

    def get_extra_addanother_params(self, request):
        return {
            'content_type': request.GET.get('content_type'),
            'object_id': request.GET.get('object_id'),
        }


class NetBoxAttachmentDeleteView(generic.ObjectDeleteView):
    queryset = models.NetBoxAttachment.objects.all()
    default_return_url = 'plugins:netbox_attachments:netboxattachment_list'
