from django.shortcuts import get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme

from netbox.views import generic
from utilities.views import register_model_view

from netbox_attachments import filtersets, forms, models, tables
from netbox_attachments.utils import get_enabled_object_type_queryset


@register_model_view(models.NetBoxAttachment, name="", detail=True)
class NetBoxAttachmentView(generic.ObjectView):
    queryset = models.NetBoxAttachment.objects.prefetch_related(
        "attachment_assignments",
        "attachment_assignments__object_type",
    )

    def get_extra_context(self, request, instance):
        assignments_table = tables.NetBoxAttachmentAssignmentTable(
            instance.attachment_assignments.all(),
            exclude=("attachment",),
        )
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
            try:
                object_type_id = int(request.GET.get("object_type", ""))
                object_id = int(request.GET.get("object_id", ""))
            except (TypeError, ValueError):
                return instance
            if object_type_id and object_id:
                object_type = get_object_or_404(get_enabled_object_type_queryset(), pk=object_type_id)
                model = object_type.model_class()
                if model is None:
                    return instance
                get_object_or_404(model, pk=object_id)
                # Pass validated assignment context to the form's save() via instance attributes
                instance._pending_object_type_id = object_type.pk
                instance._pending_object_id = object_id
        return instance

    def get_extra_addanother_params(self, request):
        return_url = request.GET.get("return_url")
        if return_url and not url_has_allowed_host_and_scheme(
            return_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return_url = None
        return {
            "object_type": request.GET.get("object_type"),
            "object_id": request.GET.get("object_id"),
            "return_url": return_url,
        }


@register_model_view(models.NetBoxAttachment, name="delete", detail=True)
class NetBoxAttachmentDeleteView(generic.ObjectDeleteView):
    queryset = models.NetBoxAttachment.objects.all()
    default_return_url = "plugins:netbox_attachments:netboxattachment_list"


@register_model_view(models.NetBoxAttachment, "bulk_edit", path="edit", detail=False)
class NetBoxAttachmentBulkEditView(generic.BulkEditView):
    queryset = models.NetBoxAttachment.objects.prefetch_related("attachment_assignments__object_type")
    filterset = filtersets.NetBoxAttachmentFilterSet
    table = tables.NetBoxAttachmentTable
    form = forms.NetBoxAttachmentBulkEditForm


@register_model_view(models.NetBoxAttachment, "bulk_delete", path="delete", detail=False)
class NetBoxAttachmentBulkDeleteView(generic.BulkDeleteView):
    queryset = models.NetBoxAttachment.objects.prefetch_related("attachment_assignments__object_type")
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
            try:
                object_type_id = int(request.GET.get("object_type", ""))
                object_id = int(request.GET.get("object_id", ""))
            except (TypeError, ValueError):
                return instance
            # Only pre-populate when both are valid integers (forward flow from a
            # detail page).  HTMX re-renders supply only object_type; they are
            # rejected above, leaving the instance untouched so the form resolves
            # the selection via get_field_value.
            if object_type_id and object_id:
                object_type = get_object_or_404(get_enabled_object_type_queryset(), pk=object_type_id)
                model = object_type.model_class()
                if model is None:
                    return instance
                get_object_or_404(model, pk=object_id)
                instance.object_type = object_type
                instance.object_id = object_id
        return instance

    def get_extra_addanother_params(self, request):
        return_url = request.GET.get("return_url")
        if return_url and not url_has_allowed_host_and_scheme(
            return_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return_url = None
        if request.GET.get("attachment"):
            # Attachment-forward flow: keep attachment pre-selected so the user
            # only needs to pick a new target object for the next assignment.
            return {"attachment": request.GET["attachment"], "return_url": return_url}
        # Object-forward flow: keep object context so the user keeps linking
        # attachments to the same object.
        return {
            "object_type": request.GET.get("object_type"),
            "object_id": request.GET.get("object_id"),
            "return_url": return_url,
        }


@register_model_view(models.NetBoxAttachmentAssignment, name="", detail=True)
class NetBoxAttachmentAssignmentView(generic.ObjectView):
    queryset = models.NetBoxAttachmentAssignment.objects.select_related("attachment", "object_type").prefetch_related(
        "tags"
    )


@register_model_view(models.NetBoxAttachmentAssignment, name="list", path="", detail=False)
class NetBoxAttachmentAssignmentListView(generic.ObjectListView):
    queryset = models.NetBoxAttachmentAssignment.objects.prefetch_related("attachment", "object_type", "tags")
    table = tables.NetBoxAttachmentAssignmentTable
    filterset = filtersets.NetBoxAttachmentAssignmentFilterSet
    filterset_form = forms.NetBoxAttachmentAssignmentFilterForm
    actions = {
        "export": set(),
        "bulk_edit": {"change"},
        "bulk_delete": {"delete"},
    }


class NetBoxAttachmentPanelListView(generic.ObjectListView):
    """Assignment list used by the inline panel (left/right/full_width display modes).

    Accepts object_type_id and object_id query params (via NetBoxAttachmentAssignmentFilterSet)
    to scope the table to a single object — mirrors what AttachmentTabView does for the tab mode.
    """

    queryset = (
        models.NetBoxAttachmentAssignment.objects.select_related("attachment")
        .prefetch_related(
            "tags",
            "attachment__tags",
        )
        .annotate(attachment_link_count=models.Count("attachment__attachment_assignments", distinct=True))
    )
    table = tables.NetBoxAttachmentForObjectTable
    filterset = filtersets.NetBoxAttachmentAssignmentFilterSet
    actions = {}


@register_model_view(models.NetBoxAttachmentAssignment, name="edit", detail=True)
class NetBoxAttachmentAssignmentEditView(generic.ObjectEditView):
    queryset = models.NetBoxAttachmentAssignment.objects.all()
    form = forms.NetBoxAttachmentAssignmentForm


@register_model_view(models.NetBoxAttachmentAssignment, "bulk_edit", path="edit", detail=False)
class NetBoxAttachmentAssignmentBulkEditView(generic.BulkEditView):
    queryset = models.NetBoxAttachmentAssignment.objects.all()
    filterset = filtersets.NetBoxAttachmentAssignmentFilterSet
    table = tables.NetBoxAttachmentAssignmentTable
    form = forms.NetBoxAttachmentAssignmentBulkEditForm


@register_model_view(models.NetBoxAttachmentAssignment, "bulk_delete", path="delete", detail=False)
class NetBoxAttachmentAssignmentBulkDeleteView(generic.BulkDeleteView):
    queryset = models.NetBoxAttachmentAssignment.objects.all()
    filterset = filtersets.NetBoxAttachmentAssignmentFilterSet
    table = tables.NetBoxAttachmentAssignmentTable
    default_return_url = "plugins:netbox_attachments:netboxattachmentassignment_list"


@register_model_view(models.NetBoxAttachmentAssignment, name="delete", detail=True)
class NetBoxAttachmentAssignmentDeleteView(generic.ObjectDeleteView):
    """
    Unlinks an attachment assignment from an object.
    The attachment itself is preserved and can be re-linked to other objects.
    """

    queryset = models.NetBoxAttachmentAssignment.objects.all()
    default_return_url = "plugins:netbox_attachments:netboxattachmentassignment_list"
