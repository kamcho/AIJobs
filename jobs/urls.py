from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/apply/', views.apply_via_email, name='apply_via_email'),
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('admin/create-job/', views.admin_create_job, name='admin_create_job'),
    path('admin/edit-job/<int:pk>/', views.admin_edit_job, name='admin_edit_job'),
]
