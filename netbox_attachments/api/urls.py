from netbox.api.routers import NetBoxRouter

from netbox_attachments.api import views

app_name = "netbox_attachments"
router = NetBoxRouter()
router.register("netbox-attachments", views.NetBoxAttachmentViewSet)
router.register("netbox-attachment-assignments", views.NetBoxAttachmentAssignmentViewSet)

urlpatterns = router.urls
