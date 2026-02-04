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
    
    # Rotas de Instituição (CRUD)
    path('instituicoes/', views.listar_instituicoes, name='listar_instituicoes'),
    path('instituicoes/cadastrar/', views.cadastrar_instituicao, name='cadastrar_instituicao'),
    path('instituicoes/<int:instituicao_id>/', views.visualizar_instituicao, name='visualizar_instituicao'),
    path('instituicoes/<int:instituicao_id>/editar/', views.editar_instituicao, name='editar_instituicao'),
    
    # Rotas de Empresa (CRUD) - Sprint 03 - TASK 22167
    path('empresas/', views.listar_empresas, name='listar_empresas'),
    path('empresas/cadastrar/', views.cadastrar_empresa, name='cadastrar_empresa'),
    path('empresas/<int:empresa_id>/', views.visualizar_empresa, name='visualizar_empresa'),
    path('empresas/<int:empresa_id>/editar/', views.editar_empresa, name='editar_empresa'),
    
    # Rotas de Supervisor (CRUD) - Sprint 03 - TASK 22168, 22169
    path('supervisores/', views.listar_supervisores, name='listar_supervisores'),
    path('supervisores/cadastrar/', views.cadastrar_supervisor, name='cadastrar_supervisor'),
    path('supervisores/<int:supervisor_id>/', views.visualizar_supervisor, name='visualizar_supervisor'),
    path('supervisores/<int:supervisor_id>/editar/', views.editar_supervisor, name='editar_supervisor'),
    
    # Painel de Estágios para Admin - Sprint 03 - TASK 22208, 22209
    path('painel-estagios/', views.painel_estagios, name='admin_painel_estagios'),
    
    # Monitoramento de Pendências para Admin - Sprint 03 - TASK 22213, 22214
    path('pendencias/', views.monitoramento_pendencias, name='admin_monitoramento_pendencias'),
]
