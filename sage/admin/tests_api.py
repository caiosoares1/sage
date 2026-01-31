"""
Testes para a API REST de Empresa e Supervisor.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from admin.models import Empresa, Supervisor
from users.models import Usuario


class EmpresaAPITestCase(APITestCase):
    """Testes para a API de Empresa"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Cria um usuário para autenticação
        self.user = Usuario.objects.create_user(
            username='testuser@test.com',
            email='testuser@test.com',
            password='testpass123',
            tipo='coordenador'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Dados de empresa válidos
        self.empresa_data = {
            'cnpj': '12345678901234',
            'razao_social': 'Empresa Teste Ltda',
            'rua': 'Rua das Flores',
            'numero': 100,
            'bairro': 'Centro'
        }
        
        # Cria uma empresa para testes
        self.empresa = Empresa.objects.create(**self.empresa_data)
    
    def test_listar_empresas(self):
        """Testa a listagem de empresas"""
        url = reverse('admin_api:empresa-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_criar_empresa_valida(self):
        """Testa a criação de uma empresa com dados válidos"""
        url = reverse('admin_api:empresa-list')
        data = {
            'cnpj': '98765432109876',
            'razao_social': 'Nova Empresa Ltda',
            'rua': 'Av. Principal',
            'numero': 200,
            'bairro': 'Industrial'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(Empresa.objects.count(), 2)
    
    def test_criar_empresa_cnpj_invalido(self):
        """Testa a criação de uma empresa com CNPJ inválido"""
        url = reverse('admin_api:empresa-list')
        data = {
            'cnpj': '123',  # CNPJ inválido
            'razao_social': 'Empresa Inválida',
            'rua': 'Rua Teste',
            'numero': 1,
            'bairro': 'Bairro'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_criar_empresa_cnpj_duplicado(self):
        """Testa a criação de uma empresa com CNPJ duplicado"""
        url = reverse('admin_api:empresa-list')
        data = self.empresa_data.copy()
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_criar_empresa_campos_obrigatorios(self):
        """CA1 - Testa que campos obrigatórios são validados"""
        url = reverse('admin_api:empresa-list')
        data = {
            'cnpj': '11111111111111',
            # Campos obrigatórios faltando
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_detalhe_empresa(self):
        """Testa a visualização de detalhes de uma empresa"""
        url = reverse('admin_api:empresa-detail', kwargs={'pk': self.empresa.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['razao_social'], self.empresa.razao_social)
    
    def test_atualizar_empresa(self):
        """Testa a atualização de uma empresa"""
        url = reverse('admin_api:empresa-detail', kwargs={'pk': self.empresa.id})
        data = {
            'cnpj': self.empresa.cnpj,
            'razao_social': 'Empresa Atualizada',
            'rua': 'Nova Rua',
            'numero': 999,
            'bairro': 'Novo Bairro'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.razao_social, 'Empresa Atualizada')
    
    def test_deletar_empresa_sem_supervisores(self):
        """Testa a exclusão de uma empresa sem supervisores"""
        url = reverse('admin_api:empresa-detail', kwargs={'pk': self.empresa.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Empresa.objects.count(), 0)
    
    def test_filtrar_empresas_por_nome(self):
        """Testa o filtro de empresas por nome"""
        url = reverse('admin_api:empresa-list')
        response = self.client.get(url, {'nome': 'Teste'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_buscar_empresas(self):
        """Testa a busca de empresas"""
        url = reverse('admin_api:empresa-list')
        response = self.client.get(url, {'search': 'Centro'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_listar_supervisores_empresa(self):
        """Testa a listagem de supervisores de uma empresa"""
        url = reverse('admin_api:empresa-supervisores', kwargs={'pk': self.empresa.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('supervisores', response.data)
    
    def test_estatisticas_empresas(self):
        """Testa as estatísticas de empresas"""
        url = reverse('admin_api:empresa-estatisticas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_empresas', response.data)


class SupervisorAPITestCase(APITestCase):
    """Testes para a API de Supervisor"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Cria um usuário para autenticação
        self.user = Usuario.objects.create_user(
            username='testuser@test.com',
            email='testuser@test.com',
            password='testpass123',
            tipo='coordenador'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Cria uma empresa
        self.empresa = Empresa.objects.create(
            cnpj='12345678901234',
            razao_social='Empresa Teste',
            rua='Rua Teste',
            numero=100,
            bairro='Centro'
        )
        
        # Dados de supervisor válidos
        self.supervisor_data = {
            'nome': 'Supervisor Teste',
            'contato': '11999999999',
            'cargo': 'Gerente',
            'empresa': self.empresa.id,
            'email': 'supervisor@teste.com',
            'senha': 'senha123'
        }
    
    def test_listar_supervisores(self):
        """Testa a listagem de supervisores"""
        url = reverse('admin_api:supervisor-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_criar_supervisor_valido(self):
        """Testa a criação de um supervisor com dados válidos"""
        url = reverse('admin_api:supervisor-list')
        response = self.client.post(url, self.supervisor_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(Supervisor.objects.count(), 1)
        # Verifica se o usuário foi criado
        self.assertTrue(Usuario.objects.filter(email='supervisor@teste.com').exists())
    
    def test_criar_supervisor_email_duplicado(self):
        """Testa que não permite criar supervisor com email duplicado"""
        # Cria o primeiro supervisor
        url = reverse('admin_api:supervisor-list')
        self.client.post(url, self.supervisor_data, format='json')
        
        # Tenta criar outro com o mesmo email
        data = self.supervisor_data.copy()
        data['nome'] = 'Outro Supervisor'
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_criar_supervisor_campos_obrigatorios(self):
        """CA3 - Testa que campos obrigatórios são validados"""
        url = reverse('admin_api:supervisor-list')
        data = {
            'email': 'novo@teste.com',
            'senha': 'senha123'
            # Nome, Cargo e Empresa faltando
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_criar_supervisor_vinculado_empresa(self):
        """CA2 - Testa que supervisor é vinculado corretamente a uma empresa"""
        url = reverse('admin_api:supervisor-list')
        response = self.client.post(url, self.supervisor_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        supervisor = Supervisor.objects.first()
        self.assertEqual(supervisor.empresa, self.empresa)
    
    def test_atualizar_supervisor(self):
        """Testa a atualização de um supervisor"""
        # Cria o supervisor primeiro
        url = reverse('admin_api:supervisor-list')
        self.client.post(url, self.supervisor_data, format='json')
        supervisor = Supervisor.objects.first()
        
        # Atualiza
        url = reverse('admin_api:supervisor-detail', kwargs={'pk': supervisor.id})
        data = {
            'nome': 'Supervisor Atualizado',
            'contato': '11888888888',
            'cargo': 'Diretor',
            'empresa': self.empresa.id
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        supervisor.refresh_from_db()
        self.assertEqual(supervisor.nome, 'Supervisor Atualizado')
    
    def test_filtrar_supervisores_por_empresa(self):
        """Testa o filtro de supervisores por empresa"""
        url = reverse('admin_api:supervisor-list')
        response = self.client.get(url, {'empresa': self.empresa.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EmpresaAPIAuthTestCase(APITestCase):
    """Testes de autenticação para a API de Empresa"""
    
    def test_listar_empresas_sem_autenticacao(self):
        """Testa que não é possível listar empresas sem autenticação"""
        url = reverse('admin_api:empresa-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_criar_empresa_sem_autenticacao(self):
        """Testa que não é possível criar empresa sem autenticação"""
        url = reverse('admin_api:empresa-list')
        data = {
            'cnpj': '12345678901234',
            'razao_social': 'Teste',
            'rua': 'Rua',
            'numero': 1,
            'bairro': 'Bairro'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
