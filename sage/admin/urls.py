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
    
    # Rotas de Empresa - MIGRADAS PARA API REST
    # Use os endpoints em /api/empresas/ para gerenciar empresas.
    # GET /api/empresas/ - Lista empresas
    # POST /api/empresas/ - Cria empresa
    # GET /api/empresas/{id}/ - Detalhe empresa
    # PUT/PATCH /api/empresas/{id}/ - Atualiza empresa
    # DELETE /api/empresas/{id}/ - Remove empresa
    
    # Rotas de Supervisor (CRUD)
    path('supervisores/', views.listar_supervisores, name='listar_supervisores'),
    path('supervisores/cadastrar/', views.cadastrar_supervisor, name='cadastrar_supervisor'),
    path('supervisores/<int:supervisor_id>/', views.visualizar_supervisor, name='visualizar_supervisor'),
    path('supervisores/<int:supervisor_id>/editar/', views.editar_supervisor, name='editar_supervisor'),
]
