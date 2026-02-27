from core.models.object_types import ObjectType
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from netbox.views import generic
from utilities.views import register_model_view

from netbox_attachments import filtersets, forms, models, tables


@register_model_view(models.NetBoxAttachment, name="", detail=True)
class NetBoxAttachmentView(generic.ObjectView):
    queryset = models.NetBoxAttachment.objects.prefetch_related(
        "attachment_assignments",
        "attachment_assignments__object_type",
    )

    def get_extra_context(self, request, instance):
        assignments_table = tables.NetBoxAttachmentAssignmentTable(instance.attachment_assignments.all())
        assignments_table.configure(request)
        return {
            "assignments_table": assignments_table,
        }


@register_model_view(models.NetBoxAttachment, name="list", path="", detail=False)
class NetBoxAttachmentListView(generic.ObjectListView):
    actions = {
        "add": {"add"},
        "export": set(),
        "bulk_edit": {"change"},
        "bulk_delete": {"delete"},
    }
    queryset = models.NetBoxAttachment.objects.prefetch_related(
        "attachment_assignments",
        "attachment_assignments__object_type",
    )
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
            # Pass assignment context to the form's save() via instance attributes
            instance._pending_object_type_id = request.GET.get("object_type")
            instance._pending_object_id = request.GET.get("object_id")
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


@register_model_view(models.NetBoxAttachment, "bulk_delete", path="delete", detail=False)
class NetBoxAttachmentBulkDeleteView(generic.BulkDeleteView):
    queryset = models.NetBoxAttachment.objects.all()
    filterset = filtersets.NetBoxAttachmentFilterSet
    table = tables.NetBoxAttachmentTable
    default_return_url = "plugins:netbox_attachments:netboxattachment_list"


class NetBoxAttachmentLinkView(generic.ObjectEditView):
    """Link an existing attachment to a NetBox object."""

    queryset = models.NetBoxAttachmentAssignment.objects.all()
    form = forms.NetBoxAttachmentLinkForm
    template_name = "netbox_attachments/netbox_attachment_link.html"
    default_return_url = "plugins:netbox_attachments:netboxattachment_list"

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            object_type_id = request.GET.get("object_type") or None
            object_id = request.GET.get("object_id") or None
            # Only pre-populate when both are provided (forward flow from a detail page).
            # When only object_type is present the request is an HTMX re-render; leave
            # the instance untouched so the form can detect the selection via get_field_value.
            if object_type_id and object_id:
                instance.object_type = get_object_or_404(ObjectType, pk=object_type_id)
                instance.object_id = object_id
        return instance

    def get_extra_addanother_params(self, request):
        return {
            "attachment": request.POST.get("attachment"),
        }


class NetBoxAttachmentAssignmentDeleteView(generic.ObjectDeleteView):
    """
    Unlinks an attachment assignment from an object.
    The attachment itself is preserved and can be re-linked to other objects.
    """

    queryset = models.NetBoxAttachmentAssignment.objects.all()
    default_return_url = "plugins:netbox_attachments:netboxattachment_list"

    def post(self, request, *args, **kwargs):
        assignment = get_object_or_404(
            models.NetBoxAttachmentAssignment.objects.restrict(request.user, "delete"),
            pk=kwargs["pk"],
        )
        attachment = assignment.attachment

        # Delete the assignment only; the attachment persists
        assignment.delete()

        messages.success(
            request,
            f"Attachment '{attachment}' has been unlinked from this object.",
        )

        return_url = request.GET.get("return_url")
        if not return_url or not url_has_allowed_host_and_scheme(return_url, allowed_hosts={request.get_host()}):
            return_url = reverse("plugins:netbox_attachments:netboxattachment_list")
        return redirect(return_url)

    def get(self, request, *args, **kwargs):
        assignment = get_object_or_404(
            models.NetBoxAttachmentAssignment.objects.restrict(request.user, "delete"),
            pk=kwargs["pk"],
        )
        attachment = assignment.attachment

        return render(
            request,
            "netbox_attachments/netboxattachmentassignment_delete.html",
            {
                "object": assignment,
                "attachment": attachment,
                "return_url": request.GET.get(
                    "return_url",
                    reverse("plugins:netbox_attachments:netboxattachment_list"),
                ),
            },
        )
