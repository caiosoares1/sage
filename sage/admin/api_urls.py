"""
URLs da API REST para o módulo admin.
Define os endpoints para Empresa e Supervisor.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import EmpresaViewSet, SupervisorViewSet

# Cria o router e registra os viewsets
router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'supervisores', SupervisorViewSet, basename='supervisor')

app_name = 'admin_api'

urlpatterns = [
    path('', include(router.urls)),
]
