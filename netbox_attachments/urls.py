from django.urls import path
from netbox.views.generic import ObjectChangeLogView

from . import models, views

urlpatterns = (
    # Files
    path('netbox-attachments/add/', views.NetBoxAttachmentEditView.as_view(),
         name='netboxattachment_add'),
    path('netbox-attachments/<int:pk>/edit/',
         views.NetBoxAttachmentEditView.as_view(), name='netboxattachment_edit'),
    path('netbox-attachments/<int:pk>/delete/',
         views.NetBoxAttachmentDeleteView.as_view(), name='netboxattachment_delete'),
    path('netbox-attachments/', views.NetBoxAttachmentListView.as_view(),
         name='netboxattachment_list'),
    path('netbox-attachments/<int:pk>/',
         views.NetBoxAttachmentView.as_view(), name='netboxattachment'),
    path('netbox-attachments/<int:pk>/changelog/', ObjectChangeLogView.as_view(),
         name='netboxattachment_changelog', kwargs={'model': models.NetBoxAttachment}),

)
