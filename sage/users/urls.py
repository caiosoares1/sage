from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Rotas de Usuário (CRUD)
    path('', views.listar_usuarios, name='listar_usuarios'),
    path('cadastrar/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('<int:usuario_id>/', views.visualizar_usuario, name='visualizar_usuario'),
    path('<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('<int:usuario_id>/atribuir-nivel/', views.atribuir_nivel_acesso, name='atribuir_nivel_acesso'),
    
    # Rotas de Nível de Acesso (CRUD) - CA1 e CA2
    path('niveis-acesso/', views.listar_niveis_acesso, name='listar_niveis_acesso'),
    path('niveis-acesso/criar/', views.criar_nivel_acesso, name='criar_nivel_acesso'),
    path('niveis-acesso/<int:nivel_id>/', views.visualizar_nivel_acesso, name='visualizar_nivel_acesso'),
    path('niveis-acesso/<int:nivel_id>/editar/', views.editar_nivel_acesso, name='editar_nivel_acesso'),
    path('niveis-acesso/<int:nivel_id>/aplicar-permissoes/', views.aplicar_permissoes_nivel, name='aplicar_permissoes_nivel'),
]
