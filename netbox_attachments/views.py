from core.models.object_types import ObjectType
from django.shortcuts import get_object_or_404
from netbox.views import generic
from utilities.views import register_model_view

from netbox_attachments import filtersets, forms, models, tables


@register_model_view(models.NetBoxAttachment, name="", detail=True)
class NetBoxAttachmentView(generic.ObjectView):
    queryset = models.NetBoxAttachment.objects.all()


@register_model_view(models.NetBoxAttachment, name="list", path="", detail=False)
class NetBoxAttachmentListView(generic.ObjectListView):
    actions = {
        "export": set(),
        "bulk_edit": {"change"},
        "bulk_delete": {"delete"},
    }
    queryset = models.NetBoxAttachment.objects.all()
    table = tables.NetBoxAttachmentTable
    filterset = filtersets.NetBoxAttachmentFilterSet
    filterset_form = forms.NetBoxAttachmentFilterForm


@register_model_view(models.NetBoxAttachment, name="add", detail=False)
@register_model_view(models.NetBoxAttachment, name="edit", detail=True)
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
            "return_url": request.GET.get("return_url"),
        }


@register_model_view(models.NetBoxAttachment, name="delete", detail=True)
class NetBoxAttachmentDeleteView(generic.ObjectDeleteView):
    queryset = models.NetBoxAttachment.objects.all()
    default_return_url = "plugins:netbox_attachments:netboxattachment_list"


@register_model_view(models.NetBoxAttachment, "bulk_edit", path="edit", detail=False)
class NetBoxAttachmentBulkEditView(generic.BulkEditView):
    queryset = models.NetBoxAttachment.objects.all()
    filterset = filtersets.NetBoxAttachmentFilterSet
    table = tables.NetBoxAttachmentTable
    form = forms.NetBoxAttachmentBulkEditForm


@register_model_view(
    models.NetBoxAttachment, "bulk_delete", path="delete", detail=False
)
class NetBoxAttachmentBulkDeleteView(generic.BulkDeleteView):
    queryset = models.NetBoxAttachment.objects.all()
    filterset = filtersets.NetBoxAttachmentFilterSet
    table = tables.NetBoxAttachmentTable
    default_return_url = "plugins:netbox_attachments:netboxattachment_list"
