from netbox.api.routers import NetBoxRouter

from . import views

app_name = 'netbox_attachments'
router = NetBoxRouter()
router.register('netbox_attachments', views.NetBoxAttachmentViewSet)

urlpatterns = router.urls
