from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('chat-history/', views.chat_history, name='chat_history'),
    path('contact/', views.contact, name='contact'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]
