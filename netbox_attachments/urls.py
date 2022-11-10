from django.urls import path
from netbox.views.generic import ObjectChangeLogView

from . import models, views

urlpatterns = (
    # Files
    path('netbox_attachments/add/', views.NetBoxAttachmentEditView.as_view(),
         name='netboxattachment_add'),
    path('netbox_attachments/<int:pk>/edit/',
         views.NetBoxAttachmentEditView.as_view(), name='netboxattachment_edit'),
    path('netbox_attachments/<int:pk>/delete/',
         views.NetBoxAttachmentDeleteView.as_view(), name='netboxattachment_delete'),
    path('netbox_attachments/', views.NetBoxAttachmentListView.as_view(), name='netboxattachment_list'),
    path('netbox_attachments/<int:pk>/', views.NetBoxAttachmentView.as_view(), name='netboxattachment'),
    path('netbox_attachments/<int:pk>/changelog/', ObjectChangeLogView.as_view(),
         name='netboxattachment_changelog', kwargs={'model': models.NetBoxAttachment}),

)
