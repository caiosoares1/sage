from django.urls import path
from . import views

urlpatterns = [
    path('solicitar/', views.solicitar_estagio, name='solicitar_estagio'),
    path('acompanhar/', views.acompanhar_estagios, name='acompanhar_estagios'),
    path('detalhe/<int:estagio_id>/', views.estagio_detalhe, name='estagio_detalhe'),
    path('documentos/', views.listar_documentos, name='listar_documentos'),
    path('documentos/<int:documento_id>/download/', views.download_documento, name='download_documento'),
    path('documentos/<int:documento_id>/historico/', views.historico_documento, name='historico_documento'),
    path('documentos/<int:documento_id>/reenviar/', views.reenviar_documento, name='reenviar_documento'),
]
