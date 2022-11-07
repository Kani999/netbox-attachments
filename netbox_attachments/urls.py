from django.urls import path

from . import views

urlpatterns = (
    # Files
    path('netbox_attachments/add/', views.NetBoxAttachmentEditView.as_view(),
         name='netbox_attachment_add'),
    path('netbox_attachments/<int:pk>/edit/',
         views.NetBoxAttachmentEditView.as_view(), name='netbox_attachment_edit'),
    path('netbox_attachments/<int:pk>/delete/',
         views.NetBoxAttachmentDeleteView.as_view(), name='netbox_attachment_delete'),
)
