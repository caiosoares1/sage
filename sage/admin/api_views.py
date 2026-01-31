"""
Views da API REST para o módulo admin.
Implementa endpoints para Empresa e Supervisor usando Django REST Framework.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from .models import Empresa, Supervisor
from .serializers import (
    EmpresaSerializer,
    EmpresaListSerializer,
    SupervisorSerializer,
    SupervisorUpdateSerializer,
    SupervisorListSerializer,
    SupervisorDetailSerializer,
)
from estagio.models import Estagio


class EmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Empresas.
    
    Endpoints:
    - GET /api/empresas/ - Lista todas as empresas
    - POST /api/empresas/ - Cria uma nova empresa
    - GET /api/empresas/{id}/ - Detalhe de uma empresa
    - PUT /api/empresas/{id}/ - Atualiza uma empresa
    - PATCH /api/empresas/{id}/ - Atualiza parcialmente uma empresa
    - DELETE /api/empresas/{id}/ - Remove uma empresa
    - GET /api/empresas/{id}/supervisores/ - Lista supervisores da empresa
    """
    queryset = Empresa.objects.all().order_by('razao_social')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cnpj']
    search_fields = ['razao_social', 'cnpj', 'bairro']
    ordering_fields = ['razao_social', 'cnpj', 'id']
    ordering = ['razao_social']
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado para cada ação"""
        if self.action == 'list':
            return EmpresaListSerializer
        return EmpresaSerializer
    
    def get_queryset(self):
        """Filtra o queryset baseado nos parâmetros da requisição"""
        queryset = super().get_queryset()
        
        # Filtro por razão social (busca parcial)
        nome = self.request.query_params.get('nome', None)
        if nome:
            queryset = queryset.filter(razao_social__icontains=nome)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Cria uma nova empresa.
        CA1 - Valida campos obrigatórios: CNPJ, rua, número, bairro e razão social
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        empresa = serializer.save()
        
        return Response(
            {
                'message': f"Empresa '{empresa.razao_social}' cadastrada com sucesso!",
                'data': EmpresaSerializer(empresa).data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Atualiza uma empresa existente.
        CA1 - Valida campos obrigatórios: CNPJ, rua, número, bairro e razão social
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        empresa = serializer.save()
        
        return Response(
            {
                'message': f"Empresa '{empresa.razao_social}' atualizada com sucesso!",
                'data': EmpresaSerializer(empresa).data
            }
        )
    
    def destroy(self, request, *args, **kwargs):
        """Remove uma empresa"""
        instance = self.get_object()
        razao_social = instance.razao_social
        
        # Verifica se há supervisores vinculados
        if instance.supervisor_set.exists():
            return Response(
                {
                    'error': 'Não é possível excluir esta empresa pois existem supervisores vinculados.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(
            {'message': f"Empresa '{razao_social}' removida com sucesso!"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def supervisores(self, request, pk=None):
        """
        Lista todos os supervisores vinculados a esta empresa.
        GET /api/empresas/{id}/supervisores/
        """
        empresa = self.get_object()
        supervisores = Supervisor.objects.filter(empresa=empresa).select_related('usuario')
        serializer = SupervisorListSerializer(supervisores, many=True)
        
        return Response({
            'empresa': EmpresaListSerializer(empresa).data,
            'supervisores': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas sobre as empresas.
        GET /api/empresas/estatisticas/
        """
        total_empresas = Empresa.objects.count()
        empresas_com_supervisores = Empresa.objects.annotate(
            num_supervisores=Count('supervisor')
        ).filter(num_supervisores__gt=0).count()
        
        empresas_com_estagios = Empresa.objects.filter(
            estagio__isnull=False
        ).distinct().count()
        
        return Response({
            'total_empresas': total_empresas,
            'empresas_com_supervisores': empresas_com_supervisores,
            'empresas_com_estagios': empresas_com_estagios,
        })


class SupervisorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Supervisores.
    
    Endpoints:
    - GET /api/supervisores/ - Lista todos os supervisores
    - POST /api/supervisores/ - Cria um novo supervisor
    - GET /api/supervisores/{id}/ - Detalhe de um supervisor
    - PUT /api/supervisores/{id}/ - Atualiza um supervisor
    - PATCH /api/supervisores/{id}/ - Atualiza parcialmente um supervisor
    - DELETE /api/supervisores/{id}/ - Remove um supervisor
    - GET /api/supervisores/{id}/estagios/ - Lista estágios do supervisor
    """
    queryset = Supervisor.objects.all().select_related('empresa', 'usuario').order_by('nome')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['empresa', 'cargo']
    search_fields = ['nome', 'cargo', 'empresa__razao_social', 'usuario__email']
    ordering_fields = ['nome', 'cargo', 'empresa__razao_social']
    ordering = ['nome']
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado para cada ação"""
        if self.action == 'list':
            return SupervisorListSerializer
        elif self.action == 'retrieve':
            return SupervisorDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return SupervisorUpdateSerializer
        return SupervisorSerializer
    
    def get_queryset(self):
        """Filtra o queryset baseado nos parâmetros da requisição"""
        queryset = super().get_queryset()
        
        # Filtro por nome (busca parcial)
        nome = self.request.query_params.get('nome', None)
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        
        # Filtro por empresa (nome da empresa)
        empresa_nome = self.request.query_params.get('empresa_nome', None)
        if empresa_nome:
            queryset = queryset.filter(empresa__razao_social__icontains=empresa_nome)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Cria um novo supervisor vinculado a uma empresa.
        CA2 - Supervisor vinculado corretamente a uma empresa
        CA3 - Valida campos obrigatórios: Nome, Cargo, Empresa, Email, Senha
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supervisor = serializer.save()
        
        return Response(
            {
                'message': f"Supervisor '{supervisor.nome}' cadastrado com sucesso!",
                'data': SupervisorDetailSerializer(supervisor).data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Atualiza um supervisor existente.
        CA3 - Valida campos obrigatórios: Nome, Cargo, Empresa
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        supervisor = serializer.save()
        
        return Response(
            {
                'message': f"Supervisor '{supervisor.nome}' atualizado com sucesso!",
                'data': SupervisorDetailSerializer(supervisor).data
            }
        )
    
    def destroy(self, request, *args, **kwargs):
        """Remove um supervisor e seu usuário associado"""
        instance = self.get_object()
        nome = instance.nome
        
        # Verifica se há estágios vinculados
        if Estagio.objects.filter(supervisor=instance).exists():
            return Response(
                {
                    'error': 'Não é possível excluir este supervisor pois existem estágios vinculados.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove o usuário associado
        usuario = instance.usuario
        self.perform_destroy(instance)
        if usuario:
            usuario.delete()
        
        return Response(
            {'message': f"Supervisor '{nome}' removido com sucesso!"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def estagios(self, request, pk=None):
        """
        Lista todos os estágios supervisionados por este supervisor.
        GET /api/supervisores/{id}/estagios/
        """
        supervisor = self.get_object()
        estagios = Estagio.objects.filter(supervisor=supervisor).select_related('empresa')
        
        estagios_data = []
        for estagio in estagios:
            estagios_data.append({
                'id': estagio.id,
                'titulo': estagio.titulo,
                'cargo': getattr(estagio, 'cargo', ''),
                'status': estagio.status,
                'data_inicio': estagio.data_inicio,
                'data_fim': estagio.data_fim,
                'empresa': estagio.empresa.razao_social if estagio.empresa else None,
            })
        
        return Response({
            'supervisor': SupervisorDetailSerializer(supervisor).data,
            'estagios': estagios_data
        })
    
    @action(detail=False, methods=['get'])
    def por_empresa(self, request):
        """
        Lista supervisores agrupados por empresa.
        GET /api/supervisores/por_empresa/
        """
        empresa_id = request.query_params.get('empresa_id', None)
        
        if empresa_id:
            supervisores = Supervisor.objects.filter(
                empresa_id=empresa_id
            ).select_related('empresa', 'usuario')
        else:
            supervisores = Supervisor.objects.all().select_related('empresa', 'usuario')
        
        serializer = SupervisorListSerializer(supervisores, many=True)
        return Response(serializer.data)
