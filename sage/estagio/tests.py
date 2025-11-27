"""
Testes para as views de aluno do sistema de estágios
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from estagio.models import Aluno, Estagio, Documento, DocumentoHistorico
from admin.models import Instituicao, Empresa, Supervisor, CursoCoordenador
from users.models import Usuario


class SolicitarEstagioViewTest(TestCase):
    """Testes para a view solicitar_estagio"""
    
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
        
        self.url = reverse('solicitar_estagio')
    
    def test_acesso_sem_autenticacao(self):
        """Testa que usuário não autenticado é redirecionado"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_acesso_com_aluno_get(self):
        """Testa que aluno autenticado pode acessar o formulário"""
        self.client.login(username='aluno@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagio_form', response.context)
        self.assertIn('documento_form', response.context)
    
    @patch('estagio.views.enviar_notificacao_email')
    def test_criar_solicitacao_com_sucesso(self, mock_email):
        """Testa criação de solicitação de estágio com documento"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        arquivo = SimpleUploadedFile(
            "termo.pdf",
            b"conteudo do pdf",
            content_type="application/pdf"
        )
        
        post_data = {
            'titulo': 'Estágio em TI',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': (date.today() + timedelta(days=7)).isoformat(),
            'data_fim': (date.today() + timedelta(days=90)).isoformat(),
            'carga_horaria': 20,
            'coordenador': self.coordenador.id,
            'arquivo': arquivo
        }
        
        response = self.client.post(self.url, post_data, follow=False)
        
        # Verificar que estágio foi criado
        estagio = Estagio.objects.filter(titulo='Estágio em TI').first()
        self.assertIsNotNone(estagio)
        self.assertEqual(estagio.status, 'analise')
        
        # Verificar que aluno foi vinculado ao estágio
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.estagio, estagio)
        
        # Verificar que documento foi criado
        documento = Documento.objects.filter(estagio=estagio).first()
        self.assertIsNotNone(documento)
        self.assertEqual(documento.versao, 1.0)
        self.assertEqual(documento.status, 'enviado')
        self.assertEqual(documento.tipo, 'termo_compromisso')
        
        # Verificar que histórico foi criado
        historico = DocumentoHistorico.objects.filter(documento=documento).first()
        self.assertIsNotNone(historico)
        self.assertEqual(historico.acao, 'enviado')
        
        # Verificar que email foi enviado
        mock_email.assert_called_once()
        
        # Verificar redirecionamento
        self.assertEqual(response.status_code, 302)
    
    def test_criar_solicitacao_com_dados_invalidos(self):
        """Testa que formulário inválido exibe erros"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        post_data = {
            'titulo': 'Estágio em TI',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': (date.today() - timedelta(days=1)).isoformat(),  # Data passada
            'data_fim': (date.today() + timedelta(days=90)).isoformat(),
            'carga_horaria': 20
        }
        
        response = self.client.post(self.url, post_data)
        
        # Verificar que não criou estágio
        self.assertEqual(Estagio.objects.count(), 0)
        
        # Verificar que exibe o formulário com erros
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagio_form', response.context)


class AcompanharEstagiosViewTest(TestCase):
    """Testes para a view acompanhar_estagios"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar instituição e empresa
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
        
        self.url = reverse('acompanhar_estagios')
    
    def test_aluno_sem_estagio(self):
        """Testa que aluno sem estágio vê lista vazia"""
        self.client.login(username='aluno@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['estagios']), 0)
        self.assertEqual(response.context['stats'], {})
    
    def test_aluno_com_estagio_sem_documentos(self):
        """Testa que aluno com estágio mas sem documentos vê estatísticas zeradas"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        # Criar estágio
        estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
        
        self.aluno.estagio = estagio
        self.aluno.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['estagios']), 1)
        self.assertEqual(response.context['stats']['total'], 0)
    
    def test_aluno_com_estagio_e_documentos(self):
        """Testa estatísticas de documentos do aluno"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        # Criar estágio
        estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
        
        self.aluno.estagio = estagio
        self.aluno.save()
        
        # Criar documentos com diferentes status
        Documento.objects.create(
            estagio=estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc1.pdf",
            tipo="termo_compromisso",
            status='enviado',
            enviado_por=self.usuario_aluno
        )
        
        Documento.objects.create(
            estagio=estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc2.pdf",
            tipo="relatorio",
            status='aprovado',
            enviado_por=self.usuario_aluno
        )
        
        Documento.objects.create(
            estagio=estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc3.pdf",
            tipo="avaliacao",
            status='finalizado',
            enviado_por=self.usuario_aluno
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats']['total'], 3)
        self.assertEqual(response.context['stats']['enviados'], 1)
        self.assertEqual(response.context['stats']['aprovados_supervisor'], 1)
        self.assertEqual(response.context['stats']['finalizados'], 1)


class EstagioDetalheViewTest(TestCase):
    """Testes para a view de detalhes do estágio"""
    
    def setUp(self):
        # Criar instituição e empresa
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
        
        # Criar estágio
        self.estagio = Estagio.objects.create(
            titulo="Estágio de Desenvolvimento",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status="analise"
        )
        
        self.aluno.estagio = self.estagio
        self.aluno.save()
    
    def test_aluno_pode_ver_detalhes_estagio(self):
        """Testa que aluno pode ver detalhes do seu estágio"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('estagio_detalhe', args=[self.estagio.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Estágio de Desenvolvimento')
        self.assertContains(response, 'Empresa Teste')
        self.assertContains(response, 'Supervisor Teste')
