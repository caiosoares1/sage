"""
Testes focados em casos de exceção e caminhos alternativos
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from users.models import Usuario
from admin.models import Instituicao, CursoCoordenador, Empresa, Supervisor
from estagio.models import Aluno, Estagio, Documento


class SolicitarEstagioExcecaoAlunoTest(TestCase):
    """Testes para exceção quando aluno não é encontrado"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar instituição
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        # Criar empresa
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste",
            cnpj="98765432109876",
            numero=456,
            bairro="Centro",
            rua="Av Teste"
        )
        
        # Criar usuário ALUNO
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        # NÃO criar o objeto Aluno para forçar a exceção
        
        usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        self.supervisor = Supervisor.objects.create(
            usuario=usuario_supervisor,
            nome="Supervisor Teste",
            contato="11988888888",
            cargo="Gerente",
            empresa=self.empresa
        )
        
        self.coordenador = CursoCoordenador.objects.create(
            usuario=usuario_coordenador,
            nome="Coordenador Teste",
            nome_curso="Ciência da Computação",
            codigo_curso=123,
            carga_horaria=40,
            contato="11977777777",
            instituicao=self.instituicao
        )
    
    @patch('estagio.views.enviar_notificacao_email')
    def test_solicitar_estagio_sem_aluno_cadastrado(self, mock_email):
        """Testa que usuário sem cadastro de aluno recebe erro"""
        # Login com usuário que não tem objeto Aluno
        self.client.login(username='aluno@test.com', password='senha123')
        
        arquivo = SimpleUploadedFile(
            "termo.pdf",
            b"conteudo do pdf",
            content_type="application/pdf"
        )
        
        post_data = {
            'titulo': 'Estágio em TI',
            'cargo': 'Desenvolvedor',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today().strftime('%Y-%m-%d'),
            'data_fim': (date.today() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'carga_horaria': 20,
            'descricao': 'Descrição do estágio',
            'coordenador': self.coordenador.id,
            'arquivo': arquivo,
        }
        
        response = self.client.post(reverse('solicitar_estagio'), post_data)
        
        # Deve redirecionar com mensagem de erro
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200 and response.context:
            messages_list = list(response.context.get('messages', []))
            # Verificar se há mensagem de erro sobre aluno não encontrado
            self.assertTrue(any('Aluno não encontrado' in str(m) for m in messages_list))


class AcompanharEstagiosExcecaoTest(TestCase):
    """Testes para exceções em acompanhar_estagios"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar usuário sem Aluno associado
        self.usuario_sem_aluno = Usuario.objects.create_user(
            username='usuario_sem_aluno@test.com',
            email='usuario_sem_aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
    
    def test_acompanhar_estagios_usuario_sem_aluno(self):
        """Testa que usuário sem Aluno vê lista vazia"""
        self.client.login(username='usuario_sem_aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('acompanhar_estagios'))
        
        # Pode redirecionar devido ao decorator @aluno_required
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            self.assertIn('estagios', response.context)
            # Deve retornar lista vazia devido à exceção
            self.assertEqual(len(response.context['estagios']), 0)


class DownloadDocumentoPermissaoTest(TestCase):
    """Testes para download_documento verificando permissões"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar instituição
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        # Criar empresa
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste",
            cnpj="98765432109876",
            numero=456,
            bairro="Centro",
            rua="Av Teste"
        )
        
        # Criar dois alunos
        self.usuario_aluno1 = Usuario.objects.create_user(
            username='aluno1@test.com',
            email='aluno1@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.usuario_aluno2 = Usuario.objects.create_user(
            username='aluno2@test.com',
            email='aluno2@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        # Criar alunos
        self.aluno1 = Aluno.objects.create(
            usuario=self.usuario_aluno1,
            nome="Aluno 1",
            matricula="20230001",
            contato="11999999999",
            instituicao=self.instituicao
        )
        
        self.aluno2 = Aluno.objects.create(
            usuario=self.usuario_aluno2,
            nome="Aluno 2",
            matricula="20230002",
            contato="11988888888",
            instituicao=self.instituicao
        )
        
        self.supervisor = Supervisor.objects.create(
            usuario=usuario_supervisor,
            nome="Supervisor Teste",
            contato="11988888888",
            cargo="Gerente",
            empresa=self.empresa
        )
        
        self.coordenador = CursoCoordenador.objects.create(
            usuario=usuario_coordenador,
            nome="Coordenador Teste",
            nome_curso="Ciência da Computação",
            codigo_curso=123,
            carga_horaria=40,
            contato="11977777777",
            instituicao=self.instituicao
        )
        
        # Criar estágios diferentes
        self.estagio1 = Estagio.objects.create(
            titulo="Estágio Aluno 1",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status="aprovado"
        )
        
        self.estagio2 = Estagio.objects.create(
            titulo="Estágio Aluno 2",
            cargo="Analista",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status="aprovado"
        )
        
        self.aluno1.estagio = self.estagio1
        self.aluno1.save()
        
        self.aluno2.estagio = self.estagio2
        self.aluno2.save()
        
        # Criar documento do aluno1
        self.documento_aluno1 = Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_aluno1.pdf",
            tipo="Plano",
            arquivo="docs/doc1.pdf",
            estagio=self.estagio1,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno1,
            status="enviado"
        )
    
    def test_aluno_nao_pode_baixar_documento_de_outro(self):
        """Testa que aluno não pode baixar documento de outro aluno"""
        self.client.login(username='aluno2@test.com', password='senha123')
        
        response = self.client.get(reverse('download_documento', args=[self.documento_aluno1.id]))
        
        # Deve redirecionar ou negar acesso
        self.assertIn(response.status_code, [302, 403, 404])


class HistoricoDocumentoVersõesTest(TestCase):
    """Testes para histórico_documento com versões"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar instituição
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        # Criar empresa
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
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        # Criar entidades
        self.aluno = Aluno.objects.create(
            usuario=self.usuario_aluno,
            nome="Aluno Teste",
            matricula="20230001",
            contato="11999999999",
            instituicao=self.instituicao
        )
        
        self.supervisor = Supervisor.objects.create(
            usuario=usuario_supervisor,
            nome="Supervisor Teste",
            contato="11988888888",
            cargo="Gerente",
            empresa=self.empresa
        )
        
        self.coordenador = CursoCoordenador.objects.create(
            usuario=usuario_coordenador,
            nome="Coordenador Teste",
            nome_curso="Ciência da Computação",
            codigo_curso=123,
            carga_horaria=40,
            contato="11977777777",
            instituicao=self.instituicao
        )
        
        # Criar estágio
        self.estagio = Estagio.objects.create(
            titulo="Estágio de Teste",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status="aprovado"
        )
        
        self.aluno.estagio = self.estagio
        self.aluno.save()
        
        # Criar documento
        self.documento = Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc.pdf",
            tipo="Plano",
            arquivo="docs/doc.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="enviado"
        )
    
    def test_historico_documento_mostra_versoes(self):
        """Testa que histórico mostra campo de versões"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('historico_documento', args=[self.documento.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('versoes', response.context)
