from django.urls import path
from . import views

app_name = 'coordenador'

urlpatterns = [
    path('solicitacoes/', views.listar_solicitacoes_coordenador, name='listar_solicitacoes_coordenador'),
    path('aprovar/<int:estagio_id>/', views.aprovar_estagio, name='aprovar_estagio'),
    path('reprovar/<int:estagio_id>/', views.reprovar_estagio, name='reprovar_estagio'),
    path('documentos/', views.aprovar_documentos_coordenador, name='documentos'),
    path('documentos/<int:documento_id>/aprovar/', views.aprovar_documento_coordenador, name='aprovar_documento'),
    
    # URLs de vínculo aluno-vaga
    path('vagas/', views.listar_vagas_disponiveis, name='listar_vagas_disponiveis'),
    path('vincular/', views.vincular_aluno_vaga, name='vincular_aluno_vaga'),
    path('vinculos/', views.listar_vinculos, name='listar_vinculos'),
    path('desvincular/<int:aluno_id>/', views.desvincular_aluno_vaga, name='desvincular_aluno_vaga'),
    path('aluno/<int:aluno_id>/historico/', views.historico_vinculo_aluno, name='historico_vinculo_aluno'),
    path('vaga/<int:vaga_id>/historico/', views.historico_vinculo_vaga, name='historico_vinculo_vaga'),
]
