from django.urls import path
from . import views
from estagio.views import cadastrar_aluno

urlpatterns = [
    path('solicitar/', views.solicitar_estagio, name='solicitar_estagio'),
    path('acompanhar/', views.acompanhar_estagios, name='acompanhar_estagios'),
    path('detalhe/<int:estagio_id>/', views.estagio_detalhe, name='estagio_detalhe'),
    path('documentos/', views.listar_documentos, name='listar_documentos'),
    path('documentos/<int:documento_id>/download/', views.download_documento, name='download_documento'),
    path('documentos/<int:documento_id>/historico/', views.historico_documento, name='historico_documento'),
    path('documentos/<int:documento_id>/reenviar/', views.reenviar_documento, name='reenviar_documento'),
    path('supervisor/horas/', views.supervisor_ver_horas, name='supervisor_ver_horas'),
    path('notificacoes/', views.listar_notificacoes, name='listar_notificacoes'),
    path('notificacoes/<int:notificacao_id>/lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    path('api/notificacoes/', views.api_notificacoes, name='api_notificacoes'),
    path('api/notificacoes/<int:notificacao_id>/lida/', views.api_marcar_notificacao_lida, name='api_marcar_notificacao_lida'),
    path('api/verificar-prazos/', views.api_verificar_prazos, name='api_verificar_prazos'),
]
