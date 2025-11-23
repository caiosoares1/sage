from django.urls import path
from . import views

urlpatterns = [
    path('solicitacoes/', views.listar_solicitacoes_coordenador, name='listar_solicitacoes_coordenador'),
    path('aprovar/<int:estagio_id>/', views.aprovar_estagio, name='aprovar_estagio'),
    path('reprovar/<int:estagio_id>/', views.reprovar_estagio, name='reprovar_estagio'),
]
