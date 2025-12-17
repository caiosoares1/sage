from django.urls import path
from . import views

app_name = 'supervisor'

urlpatterns = [
    path('documentos/', views.aprovar_documentos_supervisor, name='documentos'),
    path('documentos/<int:documento_id>/avaliar/', views.avaliar_documento, name='avaliar_documento'),
    path('documentos/<int:documento_id>/visualizar/', views.visualizar_documento_supervisor, name='visualizar_documento'),
    path('estagio/<int:estagio_id>/alterar-status/', views.alterar_status_estagio, name='alterar_status_estagio'),
]
