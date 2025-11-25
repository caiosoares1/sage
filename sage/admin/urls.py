from django.urls import path
from . import views

urlpatterns = [
    path('solicitacoes/', views.listar_solicitacoes_coordenador, name='listar_solicitacoes_coordenador'),
    path('aprovar/<int:estagio_id>/', views.aprovar_estagio, name='aprovar_estagio'),
    path('reprovar/<int:estagio_id>/', views.reprovar_estagio, name='reprovar_estagio'),
    
    # Rotas do Supervisor
    path('documentos/', views.aprovar_documentos_supervisor, name='aprovar_documentos_supervisor'),
    path('documentos/<int:documento_id>/avaliar/', views.avaliar_documento, name='avaliar_documento'),
    path('documentos/<int:documento_id>/visualizar/', views.visualizar_documento_supervisor, name='visualizar_documento_supervisor'),
    
    # Rotas do Coordenador
    path('coordenador/documentos/', views.aprovar_documentos_coordenador, name='aprovar_documentos_coordenador'),
    path('documentos/<int:documento_id>/aprovar-coordenador/', views.aprovar_documento_coordenador, name='aprovar_documento_coordenador'),
]
