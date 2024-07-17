from core.models.contenttypes import ObjectType
from django.shortcuts import get_object_or_404
from netbox.views import generic

from netbox_attachments import filtersets, forms, models, tables


class NetBoxAttachmentView(generic.ObjectView):
    controls = []
    queryset = models.NetBoxAttachment.objects.all()


class NetBoxAttachmentListView(generic.ObjectListView):
    actions = {
        "import": {"add"},
        "export": set(),
        "bulk_edit": {"change"},
        "bulk_delete": {"delete"},
    }
    queryset = models.NetBoxAttachment.objects.all()
    table = tables.NetBoxAttachmentTable
    filterset = filtersets.NetBoxAttachmentFilterSet
    filterset_form = forms.NetBoxAttachmentFilterForm


class NetBoxAttachmentEditView(generic.ObjectEditView):
    queryset = models.NetBoxAttachment.objects.all()
    form = forms.NetBoxAttachmentForm
    template_name = "netbox_attachments/netbox_attachment_edit.html"
    default_return_url = "plugins:netbox_attachments:netboxattachment_list"

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            # Assign the parent object based on URL kwargs
            instance.object_type = get_object_or_404(
                ObjectType, pk=request.GET.get("object_type")
            )
            instance.object_id = request.GET.get("object_id")

        return instance

    def get_extra_addanother_params(self, request):
        return {
            "object_type": request.GET.get("object_type"),
            "object_id": request.GET.get("object_id"),
        }


class NetBoxAttachmentDeleteView(generic.ObjectDeleteView):
    queryset = models.NetBoxAttachment.objects.all()
    default_return_url = "plugins:netbox_attachments:netboxattachment_list"
