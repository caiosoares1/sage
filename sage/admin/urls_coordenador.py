from django.urls import path
from . import views

app_name = 'coordenador'

urlpatterns = [
    path('solicitacoes/', views.listar_solicitacoes_coordenador, name='listar_solicitacoes_coordenador'),
    path('aprovar/<int:estagio_id>/', views.aprovar_estagio, name='aprovar_estagio'),
    path('reprovar/<int:estagio_id>/', views.reprovar_estagio, name='reprovar_estagio'),
    path('documentos/', views.aprovar_documentos_coordenador, name='documentos'),
    path('documentos/<int:documento_id>/aprovar/', views.aprovar_documento_coordenador, name='aprovar_documento'),
]
