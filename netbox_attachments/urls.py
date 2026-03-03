from django.urls import include, path
from utilities.urls import get_model_urls

from netbox_attachments import views

urlpatterns = (
    path(
        "netbox-attachments/",
        include(get_model_urls("netbox_attachments", "netboxattachment", detail=False)),
    ),
    path(
        "netbox-attachments/<int:pk>/",
        include(get_model_urls("netbox_attachments", "netboxattachment")),
    ),
    path(
        "netbox-attachments/link/",
        views.NetBoxAttachmentLinkView.as_view(),
        name="netboxattachment_link",
    ),
    path(
        "netbox-attachment-panel/",
        views.NetBoxAttachmentPanelListView.as_view(),
        name="netboxattachment_panel_list",
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
