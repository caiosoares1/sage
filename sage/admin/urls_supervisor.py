from django.urls import path
from . import views

app_name = 'supervisor'

urlpatterns = [
    path('documentos/', views.aprovar_documentos_supervisor, name='documentos'),
    path('documentos/<int:documento_id>/avaliar/', views.avaliar_documento, name='avaliar_documento'),
    path('documentos/<int:documento_id>/visualizar/', views.visualizar_documento_supervisor, name='visualizar_documento'),
    path('estagio/<int:estagio_id>/alterar-status/', views.alterar_status_estagio, name='alterar_status_estagio'),
    
    # Rotas de Atividades (Confirmação de cumprimento)
    path('atividades/', views.listar_atividades_pendentes, name='atividades_pendentes'),
    path('atividades/<int:atividade_id>/', views.visualizar_atividade, name='visualizar_atividade'),
    path('atividades/<int:atividade_id>/confirmar/', views.confirmar_atividade, name='confirmar_atividade'),
    path('atividades/<int:atividade_id>/rejeitar/', views.rejeitar_atividade, name='rejeitar_atividade'),
    path('atividades/<int:atividade_id>/historico/', views.historico_atividade, name='historico_atividade'),
    
    # Rotas de Avaliação de Desempenho
    path('avaliacoes/', views.listar_avaliacoes, name='listar_avaliacoes'),
    path('avaliacoes/criar/<int:aluno_id>/', views.criar_avaliacao, name='criar_avaliacao'),
    path('avaliacoes/<int:avaliacao_id>/', views.visualizar_avaliacao, name='visualizar_avaliacao'),
    path('avaliacoes/<int:avaliacao_id>/editar/', views.editar_avaliacao, name='editar_avaliacao'),
    path('avaliacoes/<int:avaliacao_id>/enviar/', views.enviar_avaliacao, name='enviar_avaliacao'),
    path('avaliacoes/<int:avaliacao_id>/excluir/', views.excluir_avaliacao, name='excluir_avaliacao'),
    
    # Rotas de Parecer Final - CA4, CA5, CA6
    path('avaliacoes/<int:avaliacao_id>/parecer/', views.emitir_parecer_final, name='emitir_parecer_final'),
    path('avaliacoes/<int:avaliacao_id>/parecer/visualizar/', views.visualizar_parecer, name='visualizar_parecer'),
    path('avaliacoes/<int:avaliacao_id>/parecer/alternar-disponibilidade/', views.alternar_disponibilidade_parecer, name='alternar_disponibilidade_parecer'),
]
