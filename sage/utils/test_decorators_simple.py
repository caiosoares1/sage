from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import redirect
from utils.decorators import supervisor_required, coordenador_required, aluno_required
from admin.models import Instituicao, Empresa, Supervisor, CursoCoordenador
from estagio.models import Aluno

Usuario = get_user_model()


class DecoratorsTestCase(TestCase):
    """Testes para decorators de autorização"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Criar instituição
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste",
            cnpj="98765432109876",
            numero=456,
            bairro="Centro",
            rua="Av Teste"
        )
        
        # Criar usuários
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        # Criar entidades relacionadas
        self.aluno = Aluno.objects.create(
            usuario=self.usuario_aluno,
            nome="Aluno Teste",
            matricula="20230001",
            contato="11999999999",
            instituicao=self.instituicao
        )
        
        self.supervisor = Supervisor.objects.create(
            usuario=self.usuario_supervisor,
            nome="Supervisor Teste",
            contato="11988888888",
            cargo="Gerente",
            empresa=self.empresa
        )
        
        self.coordenador = CursoCoordenador.objects.create(
            usuario=self.usuario_coordenador,
            nome="Coordenador Teste",
            nome_curso="Ciência da Computação",
            codigo_curso=123,
            carga_horaria=40,
            contato="11977777777",
            instituicao=self.instituicao
        )
        
        # View de teste
        @supervisor_required
        def supervisor_view(request):
            return HttpResponse("OK")
        
        @coordenador_required
        def coordenador_view(request):
            return HttpResponse("OK")
        
        @aluno_required
        def aluno_view(request):
            return HttpResponse("OK")
        
        self.supervisor_view = supervisor_view
        self.coordenador_view = coordenador_view
        self.aluno_view = aluno_view
    
    def test_supervisor_required_com_supervisor(self):
        """Testa decorator supervisor_required com supervisor autenticado"""
        request = self.factory.get('/test/')
        request.user = self.usuario_supervisor
        
        response = self.supervisor_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_supervisor_required_com_aluno(self):
        """Testa que aluno é bloqueado em área de supervisor"""
        request = self.factory.get('/test/')
        request.user = self.usuario_aluno
        
        response = self.supervisor_view(request)
        
        # Deve redirecionar
        self.assertEqual(response.status_code, 302)
    
    def test_coordenador_required_com_coordenador(self):
        """Testa decorator coordenador_required com coordenador autenticado"""
        request = self.factory.get('/test/')
        request.user = self.usuario_coordenador
        
        response = self.coordenador_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_coordenador_required_com_supervisor(self):
        """Testa que supervisor é bloqueado em área de coordenador"""
        request = self.factory.get('/test/')
        request.user = self.usuario_supervisor
        
        response = self.coordenador_view(request)
        
        # Deve redirecionar
        self.assertEqual(response.status_code, 302)
    
    def test_aluno_required_com_aluno(self):
        """Testa decorator aluno_required com aluno autenticado"""
        request = self.factory.get('/test/')
        request.user = self.usuario_aluno
        
        response = self.aluno_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_aluno_required_com_supervisor(self):
        """Testa que supervisor é bloqueado em área de aluno"""
        request = self.factory.get('/test/')
        request.user = self.usuario_supervisor
        
        response = self.aluno_view(request)
        
        # Deve redirecionar
        self.assertEqual(response.status_code, 302)
    
    def test_aluno_required_com_coordenador(self):
        """Testa que coordenador é bloqueado em área de aluno"""
        request = self.factory.get('/test/')
        request.user = self.usuario_coordenador
        
        response = self.aluno_view(request)
        
        # Deve redirecionar
        self.assertEqual(response.status_code, 302)
