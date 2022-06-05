from django.urls import path

from . import views

urlpatterns = [
    path('', views.BpmnModelListView.as_view(), name='bpmn-model-home'),
    path('bpmn_model/new', views.upload_file, name='bpmn-model-upload'),
    path('bpmn_model/<int:pk>/', views.bpmn_model_detail_view, name='bpmn-model-detail'),
    path('my-ajax-test/', views.myajaxtestview, name='ajax-test-view'),
    path('bpmn_model/new/<int:pk>/', views.choose_excel_column_headers, name='bpmn-model-column-headers'),
    path('events_log/<int:pk>/', views.events_log_detail_view, name='events-log-detail'),
]