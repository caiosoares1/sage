from django.urls import path
from . import views

urlpatterns = [
    path('solicitar/', views.solicitar_estagio, name='solicitar_estagio'),
    path('acompanhar/', views.acompanhar_estagios, name='acompanhar_estagios'),
    path('detalhe/<int:estagio_id>/', views.estagio_detalhe, name='estagio_detalhe'),
    path('documentos/', views.documentos_pendentes, name='documentos_pendentes'),
    path('documentos/<int:documento_id>/validar/', views.supervisor_validar_documento, name='supervisor_validar_documento'),
    path('documentos/<int:documento_id>/requerir-ajustes/', views.supervisor_requerir_ajustes, name='supervisor_requerir_ajustes'),
    path('documentos/<int:documento_id>/aprovar/', views.supervisor_aprovar_documento, name='supervisor_aprovar_documento'),
    path('documentos/<int:documento_id>/reprovar/', views.supervisor_reprovar_documento, name='supervisor_reprovar_documento'),
    path('documentos/<int:documento_id>/validacoes/', views.documento_validacoes, name='documento_validacoes'),
]
