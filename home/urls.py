from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
]
