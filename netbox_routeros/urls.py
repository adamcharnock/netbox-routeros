from django.urls import path
from django.views import View

from extras.views import ObjectChangeLogView
from . import views
from .models import ConfigurationTemplate

app_name = 'netbox_routeros'
urlpatterns = [

    # Regions
    path('configuration-templates/', views.ConfigurationTemplateListView.as_view(), name='configurationtemplate_list'),
    path('configuration-templates/add/', views.ConfigurationTemplateEditView.as_view(), name='configurationtemplate_add'),
    path('configuration-templates/import/', View.as_view(), name='configurationtemplate_import'),
    path('configuration-templates/delete/', View.as_view(), name='configurationtemplate_bulk_delete'),
    path('configuration-templates/<int:pk>/', views.ConfigurationTemplateView.as_view(), name='configurationtemplate'),
    path('configuration-templates/<int:pk>/edit/', views.ConfigurationTemplateEditView.as_view(), name='configurationtemplate_edit'),
    path('configuration-templates/<int:pk>/delete/', View.as_view(), name='configurationtemplate_delete'),
    path('configuration-templates/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='configurationtemplate_changelog', kwargs={'model': ConfigurationTemplate}),

]
