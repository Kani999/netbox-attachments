from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from netbox.views import generic

from . import forms, models


class NetBoxAttachmentEditView(generic.ObjectEditView):
    queryset = models.NetBoxAttachment.objects.all()
    form = forms.NetBoxAttachmentForm
    template_name = 'netbox_attachments/netbox_attachment_edit.html'

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            # Assign the parent object based on URL kwargs
            content_type = get_object_or_404(
                ContentType, pk=request.GET.get('content_type'))
            instance.parent = get_object_or_404(
                content_type.model_class(), pk=request.GET.get('object_id'))
        return instance

    def get_return_url(self, request, obj=None):
        return obj.parent.get_absolute_url() if obj else super().get_return_url(request)

    def get_extra_addanother_params(self, request):
        return {
            'content_type': request.GET.get('content_type'),
            'object_id': request.GET.get('object_id'),
        }


class NetBoxAttachmentDeleteView(generic.ObjectDeleteView):
    queryset = models.NetBoxAttachment.objects.all()

    def get_return_url(self, request, obj=None):
        return obj.parent.get_absolute_url() if obj else super().get_return_url(request)
