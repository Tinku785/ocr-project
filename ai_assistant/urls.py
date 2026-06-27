from django.urls import path

from . import views


app_name = 'ai_assistant'

urlpatterns = [
    path('', views.assistant_page, name='assistant'),
    path('chat/', views.chat, name='chat'),
    path('summarize/', views.summarize, name='summarize'),
    path('history/', views.history, name='history'),
    path('clear/', views.clear_history, name='clear_history'),
]
