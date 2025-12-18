"""
URL configuration for sage project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from estagio.views import cadastrar_aluno

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('cadastro/', cadastrar_aluno, name='cadastrar_aluno'),  # Cadastro público como aluno
    path('students/', TemplateView.as_view(template_name='dashboard.html'), name='students'),
    path('enterprises/', TemplateView.as_view(template_name='dashboard.html'), name='enterprises'),
    path('users/', TemplateView.as_view(template_name='dashboard.html'), name='users'),
    path('documents/', TemplateView.as_view(template_name='dashboard.html'), name='documents'),
    path('administrative/', TemplateView.as_view(template_name='dashboard.html'), name='administrative'),
    
    # Rotas por perfil
    path('estagio/', include('estagio.urls')),  # Aluno
    path('supervisor/', include('admin.urls_supervisor')),  # Supervisor
    path('coordenador/', include('admin.urls_coordenador')),  # Coordenador
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
