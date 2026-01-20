from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('post-job/', views.job_add, name='job_add'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/apply/', views.apply_via_email, name='apply_via_email'),
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('admin/create-job/', views.admin_create_job, name='admin_create_job'),
    path('admin/edit-job/<int:pk>/', views.admin_edit_job, name='admin_edit_job'),
    path('admin/companies/add/', views.create_company, name='create_company'),
    path('companies/<int:pk>/', views.company_detail, name='company_detail'),
    path('wishlist/', views.wishlist_list, name='wishlist_list'),
    path('wishlist/toggle/<int:pk>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('<int:pk>/analytics/', views.job_analytics, name='job_analytics'),
    path('applications/<int:pk>/status/', views.update_application_status, name='update_application_status'),
    path('<int:pk>/toggle-status/', views.toggle_job_status, name='toggle_job_status'),
    path('applications/bulk-update/', views.bulk_update_application_status, name='bulk_update_application_status'),
]
