from django.urls import path
from . import views

urlpatterns = [
    path('solicitar/', views.solicitar_estagio, name='solicitar_estagio'),
    path('acompanhar/', views.acompanhar_estagios, name='acompanhar_estagios'),
    path('historico-solicitacoes/', views.historico_solicitacoes, name='historico_solicitacoes'),
    path('detalhe/<int:estagio_id>/', views.estagio_detalhe, name='estagio_detalhe'),
    path('detalhe/<int:estagio_id>/historico/', views.historico_estagio, name='historico_estagio'),
    path('documentos/', views.listar_documentos, name='listar_documentos'),
    path('documentos/<int:documento_id>/download/', views.download_documento, name='download_documento'),
    path('documentos/<int:documento_id>/historico/', views.historico_documento, name='historico_documento'),
    path('documentos/<int:documento_id>/reenviar/', views.reenviar_documento, name='reenviar_documento'),
    path('supervisor/horas/', views.supervisor_ver_horas, name='supervisor_ver_horas'),
    path('notificacoes/', views.listar_notificacoes, name='listar_notificacoes'),
    path('notificacoes/<int:notificacao_id>/lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    path('api/notificacoes/', views.api_notificacoes, name='api_notificacoes'),
    path('api/notificacoes-nao-lidas/', views.api_contar_notificacoes_nao_lidas, name='api_contar_notificacoes_nao_lidas'),
    path('api/notificacoes/<int:notificacao_id>/lida/', views.api_marcar_notificacao_lida, name='api_marcar_notificacao_lida'),
    path('api/verificar-prazos/', views.api_verificar_prazos, name='api_verificar_prazos'),
    
    # Rotas de edição do aluno (cadastro movido para rota pública /cadastro/)
    path('aluno/editar/', views.editar_dados_aluno, name='editar_dados_aluno'),
    
    # Rotas de horas do aluno (Tasks 20926, 20928, 20929, 20932, 20937)
    path('horas/cadastrar/', views.cadastrar_horas, name='cadastrar_horas'),
    path('horas/consultar/', views.consultar_horas, name='consultar_horas'),
    
    # Rotas de feedbacks do supervisor (Tasks 20939, 20940, 20943)
    path('feedbacks/', views.listar_feedbacks, name='listar_feedbacks'),
    path('supervisor/enviar-feedback/', views.enviar_feedback_aluno, name='enviar_feedback_aluno'),
    path('supervisor/enviar-feedback/<int:aluno_id>/', views.enviar_feedback_aluno, name='enviar_feedback_aluno_especifico'),
    
    # Rotas de Consulta de Pareceres - CA6
    path('pareceres/', views.listar_pareceres_aluno, name='listar_pareceres_aluno'),
    path('pareceres/<int:avaliacao_id>/', views.consultar_parecer, name='consultar_parecer'),
    
    # Rotas do Painel de Status de Estágios - CA1, CA2, CA3
    path('painel/', views.painel_estagios, name='painel_estagios'),
    path('api/painel/', views.api_painel_estagios, name='api_painel_estagios'),
    path('api/painel/estatisticas/', views.api_estatisticas_estagios, name='api_estatisticas_estagios'),
    path('api/painel/status/<str:status>/', views.api_estagios_por_status, name='api_estagios_por_status'),
    
    # Rotas do Monitoramento de Pendências e Resultados - CA4, CA5, CA6
    path('monitoramento/', views.monitoramento_pendencias, name='monitoramento_pendencias'),
    path('api/monitoramento/', views.api_monitoramento_pendencias, name='api_monitoramento_pendencias'),
    path('api/monitoramento/tipo/<str:tipo>/', views.api_pendencias_por_tipo, name='api_pendencias_por_tipo'),
    path('api/monitoramento/resultados/', views.api_resultados_consolidados, name='api_resultados_consolidados'),
    
    # Rotas de Geração de Relatórios de Estágios - CA1, CA2, CA3
    path('relatorios/', views.gerar_relatorio_estagios, name='gerar_relatorio_estagios'),
    path('api/relatorios/', views.api_relatorio_estagios, name='api_relatorio_estagios'),
    path('api/relatorios/exportar/', views.api_relatorio_exportar, name='api_relatorio_exportar'),
    
    # ========== Sprint 03 - Novas Rotas ==========
    
    # Rotas de Vagas Disponíveis - TASK 22173, 22174
    path('vagas/', views.listar_vagas_disponiveis, name='listar_vagas_disponiveis'),
    path('vagas/<int:estagio_id>/', views.detalhe_vaga, name='detalhe_vaga'),
    path('vagas/<int:estagio_id>/selecionar-aluno/', views.selecionar_aluno_vaga, name='selecionar_aluno_vaga'),
    path('vagas/<int:estagio_id>/vincular/', views.vincular_aluno_vaga, name='vincular_aluno_vaga'),
    
    # Rotas de Atividades Pendentes - TASK 22180, 22181, 22182
    path('atividades/', views.listar_atividades_pendentes, name='listar_atividades_pendentes'),
    path('atividades/<int:atividade_id>/', views.detalhe_atividade, name='detalhe_atividade'),
    path('atividades/<int:atividade_id>/confirmar/', views.confirmar_atividade, name='confirmar_atividade'),
    path('atividades/<int:atividade_id>/rejeitar/', views.rejeitar_atividade, name='rejeitar_atividade'),
    
    # Rotas de Avaliação e Parecer - TASK 22186, 22191, 22193
    path('avaliacao/<int:estagio_id>/criar/', views.formulario_avaliacao, name='formulario_avaliacao'),
    path('avaliacao/<int:avaliacao_id>/parecer/', views.emitir_parecer, name='emitir_parecer'),
    path('avaliacao/<int:avaliacao_id>/', views.visualizar_avaliacao, name='visualizar_avaliacao'),
]
