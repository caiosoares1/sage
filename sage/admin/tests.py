"""
Testes para as views de supervisor e coordenador do sistema de estágios
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from datetime import date, timedelta
from unittest.mock import patch
from estagio.models import Aluno, Estagio, Documento, DocumentoHistorico
from admin.models import Instituicao, Empresa, Supervisor, CursoCoordenador
from users.models import Usuario


class AprovarDocumentosSupervisorViewTest(TestCase):
    """Testes para a view aprovar_documentos_supervisor"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar dados de teste
        instituicao = Instituicao.objects.create(
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
        
        self.usuario_supervisor = Usuario.objects.create_user(
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
            usuario=self.usuario_supervisor,
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
            instituicao=instituicao
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
        
        self.url = reverse('supervisor:documentos')
    
    def test_acesso_com_supervisor(self):
        """Testa que supervisor tem acesso à página"""
        self.client.login(username='supervisor@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('documentos', response.context)
        self.assertIn('stats', response.context)
    
    def test_estatisticas_documentos(self):
        """Testa cálculo de estatísticas de documentos"""
        self.client.login(username='supervisor@test.com', password='senha123')
        
        usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        # Criar documentos com diferentes status
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc1.pdf",
            tipo="termo_compromisso",
            status='enviado',
            enviado_por=usuario_aluno
        )
        
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc2.pdf",
            tipo="relatorio",
            status='aprovado',
            enviado_por=usuario_aluno
        )
        
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc3.pdf",
            tipo="avaliacao",
            status='reprovado',
            enviado_por=usuario_aluno
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['pendentes'], 1)
        self.assertEqual(stats['aprovados'], 1)
        self.assertEqual(stats['reprovados'], 1)


class AprovarDocumentosCoordenadorViewTest(TestCase):
    """Testes para a view aprovar_documentos_coordenador"""
    
    def setUp(self):
        self.client = Client()
        
        instituicao = Instituicao.objects.create(
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
        
        usuario_aluno = Usuario.objects.create_user(
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
        
        self.usuario_coordenador = Usuario.objects.create_user(
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
            usuario=self.usuario_coordenador,
            nome="Coordenador Teste",
            nome_curso="Ciência da Computação",
            codigo_curso=123,
            carga_horaria=40,
            contato="11977777777",
            instituicao=instituicao
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
        
        self.url = reverse('coordenador:documentos')
    
    def test_acesso_com_coordenador(self):
        """Testa que coordenador tem acesso à página"""
        self.client.login(username='coordenador@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('documentos', response.context)
    
    @patch('admin.views.enviar_notificacao_email')
    def test_aprovar_documento_coordenador(self, mock_email):
        """Testa aprovação final de documento pelo coordenador"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        # Criar documento aprovado pelo supervisor
        documento = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo.pdf",
            tipo="termo_compromisso",
            status='aprovado',  # Já aprovado pelo supervisor
            enviado_por=Usuario.objects.create_user(
                username='aluno2@test.com',
                email='aluno2@test.com',
                password='senha123',
                tipo='aluno'
            )
        )
        
        url = reverse('coordenador:aprovar_documento', args=[documento.id])
        response = self.client.post(url)
        
        # Verificar que documento foi finalizado
        documento.refresh_from_db()
        self.assertEqual(documento.status, 'finalizado')
        
        # Verificar redirecionamento
        self.assertEqual(response.status_code, 302)


class AprovarEstagioViewTest(TestCase):
    """Testes para as views de aprovação/reprovação de estágio"""
    
    def setUp(self):
        self.client = Client()
        
        instituicao = Instituicao.objects.create(
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
        
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.supervisor = Supervisor.objects.create(
            usuario=usuario_supervisor,
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
            instituicao=instituicao
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='analise'
        )
    
    @patch('admin.views.enviar_notificacao_email')
    def test_aprovar_estagio(self, mock_email):
        """Testa aprovação de estágio"""
        self.client.login(username='coordenador@test.com', password='senha123')
        url = reverse('coordenador:aprovar_estagio', args=[self.estagio.id])
        
        response = self.client.get(url)
        
        # Verificar que estágio foi aprovado
        self.estagio.refresh_from_db()
        self.assertEqual(self.estagio.status, 'aprovado')
        
        # Verificar que email foi enviado
        mock_email.assert_called_once()
        
        # Verificar redirecionamento
        self.assertEqual(response.status_code, 302)
    
    @patch('admin.views.enviar_notificacao_email')
    def test_reprovar_estagio(self, mock_email):
        """Testa reprovação de estágio"""
        self.client.login(username='coordenador@test.com', password='senha123')
        url = reverse('coordenador:reprovar_estagio', args=[self.estagio.id])
        
        response = self.client.get(url)
        
        # Verificar que estágio foi reprovado
        self.estagio.refresh_from_db()
        self.assertEqual(self.estagio.status, 'reprovado')
        
        # Verificar que email foi enviado
        mock_email.assert_called_once()
        
        # Verificar redirecionamento
        self.assertEqual(response.status_code, 302)


class RegistrarHistoricoTest(TestCase):
    """Testes para a função registrar_historico"""
    
    def setUp(self):
        # Criar dados de teste
        instituicao = Instituicao.objects.create(
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
        
        self.usuario = Usuario.objects.create_user(
            username='usuario@test.com',
            email='usuario@test.com',
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
            usuario=self.usuario,
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
            instituicao=instituicao
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
        
        self.documento = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo.pdf",
            tipo="termo_compromisso",
            enviado_por=self.usuario
        )
    
    def test_registrar_historico_sem_observacoes(self):
        """Testa registro de histórico sem observações"""
        from admin.views import registrar_historico
        
        registrar_historico(
            documento=self.documento,
            acao='aprovado',
            usuario=self.usuario
        )
        
        historico = DocumentoHistorico.objects.filter(
            documento=self.documento,
            acao='aprovado'
        ).first()
        
        self.assertIsNotNone(historico)
        self.assertEqual(historico.usuario, self.usuario)
        self.assertIsNone(historico.observacoes)
    
    def test_registrar_historico_com_observacoes(self):
        """Testa registro de histórico com observações"""
        from admin.views import registrar_historico
        
        observacoes = "Documento aprovado após revisão"
        registrar_historico(
            documento=self.documento,
            acao='aprovado',
            usuario=self.usuario,
            observacoes=observacoes
        )
        
        historico = DocumentoHistorico.objects.filter(
            documento=self.documento,
            acao='aprovado'
        ).first()
        
        self.assertIsNotNone(historico)
        self.assertEqual(historico.observacoes, observacoes)
