from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_document, name='upload_document'),
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    path('document/<int:pk>/delete/', views.delete_document, name='delete_document'),
    path('document/<int:pk>/edit/', views.edit_document, name='edit_document'),
    path('search/', views.search_documents, name='search_documents'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('document/<int:pk>/export/txt/', views.export_txt, name='export_txt'),
    path('document/<int:pk>/export/pdf/', views.export_pdf, name='export_pdf'),
    path('document/<int:pk>/retry/', views.retry_document, name='retry_document'),
]