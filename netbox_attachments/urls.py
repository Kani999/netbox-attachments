from django.urls import include, path
from utilities.urls import get_model_urls

from netbox_attachments import views

urlpatterns = (
    path(
        "netbox-attachments/",
        views.NetBoxAttachmentListView.as_view(),
        name="netboxattachment_list",
    ),
    path(
        "netbox-attachments/add/",
        views.NetBoxAttachmentEditView.as_view(),
        name="netboxattachment_add",
    ),
    path(
        "netbox-attachments/link/",
        views.NetBoxAttachmentLinkView.as_view(),
        name="netboxattachment_link",
    ),
    path(
        "netbox-attachments/edit/",
        views.NetBoxAttachmentBulkEditView.as_view(),
        name="netboxattachment_bulk_edit",
    ),
    path(
        "netbox-attachments/delete/",
        views.NetBoxAttachmentBulkDeleteView.as_view(),
        name="netboxattachment_bulk_delete",
    ),
    path(
        "netbox-attachments/<int:pk>/",
        views.NetBoxAttachmentView.as_view(),
        name="netboxattachment",
    ),
    path(
        "netbox-attachments/<int:pk>/edit/",
        views.NetBoxAttachmentEditView.as_view(),
        name="netboxattachment_edit",
    ),
    path(
        "netbox-attachments/<int:pk>/delete/",
        views.NetBoxAttachmentDeleteView.as_view(),
        name="netboxattachment_delete",
    ),
    path(
        "netbox-attachments/",
        include(get_model_urls("netbox_attachments", "netboxattachment", detail=False)),
    ),
    path(
        "netbox-attachments/<int:pk>/",
        include(get_model_urls("netbox_attachments", "netboxattachment")),
    ),
    # Assignment views
    path(
        "netbox-attachment-assignments/",
        views.NetBoxAttachmentAssignmentListView.as_view(),
        name="netboxattachmentassignment_list",
    ),
    path(
        "netbox-attachment-assignments/<int:pk>/delete/",
        views.NetBoxAttachmentAssignmentDeleteView.as_view(),
        name="netboxattachmentassignment_delete",
    ),
)
