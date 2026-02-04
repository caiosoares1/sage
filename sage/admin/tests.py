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


# ==================== TESTES DE EMPRESA ====================

class ValidarCNPJTest(TestCase):
    """Testes para a função validar_cnpj"""
    
    def test_cnpj_valido_14_digitos(self):
        """Testa CNPJ válido com 14 dígitos"""
        from admin.forms import validar_cnpj
        
        self.assertTrue(validar_cnpj("12345678901234"))
    
    def test_cnpj_valido_com_mascara(self):
        """Testa CNPJ válido com máscara de formatação"""
        from admin.forms import validar_cnpj
        
        self.assertTrue(validar_cnpj("12.345.678/9012-34"))
    
    def test_cnpj_invalido_menos_digitos(self):
        """Testa CNPJ inválido com menos de 14 dígitos"""
        from admin.forms import validar_cnpj
        
        self.assertFalse(validar_cnpj("1234567890123"))
    
    def test_cnpj_invalido_mais_digitos(self):
        """Testa CNPJ inválido com mais de 14 dígitos"""
        from admin.forms import validar_cnpj
        
        self.assertFalse(validar_cnpj("123456789012345"))
    
    def test_cnpj_invalido_todos_iguais(self):
        """Testa CNPJ inválido com todos os dígitos iguais"""
        from admin.forms import validar_cnpj
        
        self.assertFalse(validar_cnpj("00000000000000"))
        self.assertFalse(validar_cnpj("11111111111111"))


class ListarEmpresasViewTest(TestCase):
    """Testes para a view listar_empresas"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
        self.url = reverse('listar_empresas')
    
    def test_listar_empresas_requer_login(self):
        """Testa que a listagem requer autenticação"""
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])
    
    def test_listar_empresas_com_login(self):
        """Testa listagem de empresas com usuário autenticado"""
        self.client.login(username='admin@test.com', password='senha123')
        
        # Criar empresas de teste
        Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa A",
            rua="Rua A",
            numero=100,
            bairro="Centro"
        )
        Empresa.objects.create(
            cnpj="98765432109876",
            razao_social="Empresa B",
            rua="Rua B",
            numero=200,
            bairro="Jardim"
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('empresas', response.context)
        self.assertEqual(len(response.context['empresas']), 2)
    
    def test_filtrar_empresas_por_nome(self):
        """Testa filtro de empresas por razão social"""
        self.client.login(username='admin@test.com', password='senha123')
        
        Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Tech Solutions",
            rua="Rua A",
            numero=100,
            bairro="Centro"
        )
        Empresa.objects.create(
            cnpj="98765432109876",
            razao_social="Comercio Brasil",
            rua="Rua B",
            numero=200,
            bairro="Jardim"
        )
        
        response = self.client.get(self.url, {'razao': 'Tech'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['empresas']), 1)
        self.assertEqual(response.context['empresas'][0].razao_social, "Tech Solutions")


class CadastrarEmpresaViewTest(TestCase):
    """Testes para a view cadastrar_empresa - CA1"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
        self.url = reverse('cadastrar_empresa')
    
    def test_cadastrar_empresa_get(self):
        """Testa acesso GET ao formulário de cadastro"""
        self.client.login(username='admin@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_cadastrar_empresa_sucesso(self):
        """Testa cadastro de empresa com sucesso - CA1"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Nova Empresa LTDA',
            'rua': 'Rua das Flores',
            'numero': '123',
            'bairro': 'Centro'
        }
        
        response = self.client.post(self.url, dados)
        
        # Verifica redirecionamento após sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verifica que a empresa foi criada
        empresa = Empresa.objects.get(cnpj='12345678901234')
        self.assertEqual(empresa.razao_social, 'Nova Empresa LTDA')
        self.assertEqual(empresa.rua, 'Rua das Flores')
        self.assertEqual(empresa.numero, 123)
        self.assertEqual(empresa.bairro, 'Centro')
    
    def test_cadastrar_empresa_cnpj_obrigatorio(self):
        """Testa validação de CNPJ obrigatório - CA1"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '',
            'razao_social': 'Empresa Teste',
            'rua': 'Rua Teste',
            'numero': '100',
            'bairro': 'Bairro Teste'
        }
        
        response = self.client.post(self.url, dados)
        
        # Deve permanecer na página com erro
        self.assertEqual(response.status_code, 200)
        
        # Verifica mensagem de erro
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('CNPJ é obrigatório' in str(m) for m in messages_list))
        
        # Verifica que empresa não foi criada
        self.assertEqual(Empresa.objects.count(), 0)
    
    def test_cadastrar_empresa_cnpj_invalido(self):
        """Testa validação de CNPJ inválido - CA1"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '123',  # CNPJ com menos de 14 dígitos
            'razao_social': 'Empresa Teste',
            'rua': 'Rua Teste',
            'numero': '100',
            'bairro': 'Bairro Teste'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('CNPJ inválido' in str(m) for m in messages_list))
        self.assertEqual(Empresa.objects.count(), 0)
    
    def test_cadastrar_empresa_razao_social_obrigatoria(self):
        """Testa validação de razão social obrigatória - CA1"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': '',
            'rua': 'Rua Teste',
            'numero': '100',
            'bairro': 'Bairro Teste'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Razão Social é obrigatória' in str(m) for m in messages_list))
        self.assertEqual(Empresa.objects.count(), 0)
    
    def test_cadastrar_empresa_rua_obrigatoria(self):
        """Testa validação de rua obrigatória - CA1"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Empresa Teste',
            'rua': '',
            'numero': '100',
            'bairro': 'Bairro Teste'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Rua é obrigatória' in str(m) for m in messages_list))
        self.assertEqual(Empresa.objects.count(), 0)
    
    def test_cadastrar_empresa_numero_obrigatorio(self):
        """Testa validação de número obrigatório - CA1"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Empresa Teste',
            'rua': 'Rua Teste',
            'numero': '',
            'bairro': 'Bairro Teste'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Número é obrigatório' in str(m) for m in messages_list))
        self.assertEqual(Empresa.objects.count(), 0)
    
    def test_cadastrar_empresa_bairro_obrigatorio(self):
        """Testa validação de bairro obrigatório - CA1"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Empresa Teste',
            'rua': 'Rua Teste',
            'numero': '100',
            'bairro': ''
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Bairro é obrigatório' in str(m) for m in messages_list))
        self.assertEqual(Empresa.objects.count(), 0)
    
    def test_cadastrar_empresa_cnpj_duplicado(self):
        """Testa validação de CNPJ duplicado"""
        self.client.login(username='admin@test.com', password='senha123')
        
        # Criar empresa existente
        Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Existente",
            rua="Rua Existente",
            numero=100,
            bairro="Bairro Existente"
        )
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Nova Empresa',
            'rua': 'Rua Nova',
            'numero': '200',
            'bairro': 'Bairro Novo'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Já existe uma empresa cadastrada com este CNPJ' in str(m) for m in messages_list))
        self.assertEqual(Empresa.objects.count(), 1)
    
    def test_cadastrar_empresa_numero_invalido(self):
        """Testa validação de número inválido"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Empresa Teste',
            'rua': 'Rua Teste',
            'numero': 'abc',  # Valor não numérico
            'bairro': 'Bairro Teste'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Número deve ser um valor numérico' in str(m) for m in messages_list))


class VisualizarEmpresaViewTest(TestCase):
    """Testes para a view visualizar_empresa"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        self.url = reverse('visualizar_empresa', args=[self.empresa.id])
    
    def test_visualizar_empresa_existente(self):
        """Testa visualização de empresa existente"""
        self.client.login(username='admin@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('empresa', response.context)
        self.assertEqual(response.context['empresa'].razao_social, 'Empresa Teste')
    
    def test_visualizar_empresa_inexistente(self):
        """Testa visualização de empresa inexistente retorna 404"""
        self.client.login(username='admin@test.com', password='senha123')
        url = reverse('visualizar_empresa', args=[9999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class EditarEmpresaViewTest(TestCase):
    """Testes para a view editar_empresa"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Original",
            rua="Rua Original",
            numero=100,
            bairro="Bairro Original"
        )
        self.url = reverse('editar_empresa', args=[self.empresa.id])
    
    def test_editar_empresa_get(self):
        """Testa acesso GET ao formulário de edição"""
        self.client.login(username='admin@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('empresa', response.context)
    
    def test_editar_empresa_sucesso(self):
        """Testa edição de empresa com sucesso"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '98765432109876',
            'razao_social': 'Empresa Atualizada',
            'rua': 'Rua Atualizada',
            'numero': '200',
            'bairro': 'Bairro Atualizado'
        }
        
        response = self.client.post(self.url, dados)
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica dados atualizados
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.razao_social, 'Empresa Atualizada')
        self.assertEqual(self.empresa.cnpj, '98765432109876')
    
    def test_editar_empresa_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios na edição - CA1"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'cnpj': '',
            'razao_social': '',
            'rua': '',
            'numero': '',
            'bairro': ''
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages_list) >= 5)  # Deve ter pelo menos 5 erros


# ==================== TESTES DE SUPERVISOR ====================

class ListarSupervisoresViewTest(TestCase):
    """Testes para a view listar_supervisores"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        self.url = reverse('listar_supervisores')
    
    def test_listar_supervisores_com_login(self):
        """Testa listagem de supervisores com usuário autenticado"""
        self.client.login(username='admin@test.com', password='senha123')
        
        # Criar supervisor de teste
        usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        Supervisor.objects.create(
            nome="João Silva",
            contato="11999999999",
            cargo="Gerente",
            empresa=self.empresa,
            usuario=usuario_supervisor
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('supervisores', response.context)
        self.assertEqual(len(response.context['supervisores']), 1)


class CadastrarSupervisorViewTest(TestCase):
    """Testes para a view cadastrar_supervisor - CA2 e CA3"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        self.url = reverse('cadastrar_supervisor')
    
    def test_cadastrar_supervisor_get(self):
        """Testa acesso GET ao formulário de cadastro"""
        self.client.login(username='admin@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('empresas', response.context)
    
    def test_cadastrar_supervisor_sucesso(self):
        """Testa cadastro de supervisor com sucesso - CA2"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'nome': 'Carlos Supervisor',
            'contato': '11988887777',
            'cargo': 'Coordenador de Estágio',
            'empresa': str(self.empresa.id),
            'email': 'carlos.supervisor@empresa.com',
            'senha': 'senha123456'
        }
        
        response = self.client.post(self.url, dados)
        
        # Verifica redirecionamento após sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verifica que o supervisor foi criado
        supervisor = Supervisor.objects.get(nome='Carlos Supervisor')
        self.assertEqual(supervisor.cargo, 'Coordenador de Estágio')
        self.assertEqual(supervisor.empresa, self.empresa)
        
        # Verifica que o usuário foi criado corretamente
        usuario = supervisor.usuario
        self.assertEqual(usuario.email, 'carlos.supervisor@empresa.com')
        self.assertEqual(usuario.tipo, 'supervisor')
    
    def test_cadastrar_supervisor_nome_obrigatorio(self):
        """Testa validação de nome obrigatório - CA3"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'nome': '',
            'contato': '11988887777',
            'cargo': 'Gerente',
            'empresa': str(self.empresa.id),
            'email': 'supervisor@empresa.com',
            'senha': 'senha123456'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Nome é obrigatório' in str(m) for m in messages_list))
        self.assertEqual(Supervisor.objects.count(), 0)
    
    def test_cadastrar_supervisor_cargo_obrigatorio(self):
        """Testa validação de cargo obrigatório - CA3"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'nome': 'Carlos Supervisor',
            'contato': '11988887777',
            'cargo': '',
            'empresa': str(self.empresa.id),
            'email': 'supervisor@empresa.com',
            'senha': 'senha123456'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Cargo é obrigatório' in str(m) for m in messages_list))
        self.assertEqual(Supervisor.objects.count(), 0)
    
    def test_cadastrar_supervisor_empresa_obrigatoria(self):
        """Testa validação de empresa obrigatória - CA3"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'nome': 'Carlos Supervisor',
            'contato': '11988887777',
            'cargo': 'Gerente',
            'empresa': '',
            'email': 'supervisor@empresa.com',
            'senha': 'senha123456'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Empresa é obrigatória' in str(m) for m in messages_list))
        self.assertEqual(Supervisor.objects.count(), 0)
    
    def test_cadastrar_supervisor_empresa_inexistente(self):
        """Testa validação de empresa inexistente"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'nome': 'Carlos Supervisor',
            'contato': '11988887777',
            'cargo': 'Gerente',
            'empresa': '9999',  # ID que não existe
            'email': 'supervisor@empresa.com',
            'senha': 'senha123456'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Empresa selecionada não existe' in str(m) for m in messages_list))
    
    def test_cadastrar_supervisor_email_duplicado(self):
        """Testa validação de email duplicado"""
        self.client.login(username='admin@test.com', password='senha123')
        
        # Criar usuário existente
        Usuario.objects.create_user(
            username='existente@empresa.com',
            email='existente@empresa.com',
            password='senha123',
            tipo='supervisor'
        )
        
        dados = {
            'nome': 'Carlos Supervisor',
            'contato': '11988887777',
            'cargo': 'Gerente',
            'empresa': str(self.empresa.id),
            'email': 'existente@empresa.com',
            'senha': 'senha123456'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Já existe um usuário cadastrado com este email' in str(m) for m in messages_list))
    
    def test_cadastrar_supervisor_senha_curta(self):
        """Testa validação de senha com menos de 6 caracteres"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'nome': 'Carlos Supervisor',
            'contato': '11988887777',
            'cargo': 'Gerente',
            'empresa': str(self.empresa.id),
            'email': 'supervisor@empresa.com',
            'senha': '12345'  # Senha curta
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Senha deve ter pelo menos 6 caracteres' in str(m) for m in messages_list))
    
    def test_cadastrar_supervisor_vinculo_empresa_correto(self):
        """Testa que supervisor é vinculado corretamente à empresa - CA2"""
        self.client.login(username='admin@test.com', password='senha123')
        
        # Criar outra empresa
        empresa2 = Empresa.objects.create(
            cnpj="98765432109876",
            razao_social="Outra Empresa",
            rua="Outra Rua",
            numero=200,
            bairro="Outro Bairro"
        )
        
        dados = {
            'nome': 'Carlos Supervisor',
            'contato': '11988887777',
            'cargo': 'Gerente',
            'empresa': str(empresa2.id),  # Vincula à segunda empresa
            'email': 'carlos@outraempresa.com',
            'senha': 'senha123456'
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 302)
        
        supervisor = Supervisor.objects.get(nome='Carlos Supervisor')
        self.assertEqual(supervisor.empresa.id, empresa2.id)
        self.assertEqual(supervisor.empresa.razao_social, 'Outra Empresa')


class VisualizarSupervisorViewTest(TestCase):
    """Testes para a view visualizar_supervisor"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        self.supervisor = Supervisor.objects.create(
            nome="João Silva",
            contato="11999999999",
            cargo="Gerente",
            empresa=self.empresa,
            usuario=usuario_supervisor
        )
        self.url = reverse('visualizar_supervisor', args=[self.supervisor.id])
    
    def test_visualizar_supervisor_existente(self):
        """Testa visualização de supervisor existente"""
        self.client.login(username='admin@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('supervisor', response.context)
        self.assertEqual(response.context['supervisor'].nome, 'João Silva')
    
    def test_visualizar_supervisor_inexistente(self):
        """Testa visualização de supervisor inexistente retorna 404"""
        self.client.login(username='admin@test.com', password='senha123')
        url = reverse('visualizar_supervisor', args=[9999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class EditarSupervisorViewTest(TestCase):
    """Testes para a view editar_supervisor"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Original",
            rua="Rua Original",
            numero=100,
            bairro="Centro"
        )
        usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        self.supervisor = Supervisor.objects.create(
            nome="Nome Original",
            contato="11999999999",
            cargo="Cargo Original",
            empresa=self.empresa,
            usuario=usuario_supervisor
        )
        self.url = reverse('editar_supervisor', args=[self.supervisor.id])
    
    def test_editar_supervisor_get(self):
        """Testa acesso GET ao formulário de edição"""
        self.client.login(username='admin@test.com', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('supervisor', response.context)
        self.assertIn('empresas', response.context)
    
    def test_editar_supervisor_sucesso(self):
        """Testa edição de supervisor com sucesso"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'nome': 'Nome Atualizado',
            'contato': '11888888888',
            'cargo': 'Cargo Atualizado',
            'empresa': str(self.empresa.id)
        }
        
        response = self.client.post(self.url, dados)
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica dados atualizados
        self.supervisor.refresh_from_db()
        self.assertEqual(self.supervisor.nome, 'Nome Atualizado')
        self.assertEqual(self.supervisor.cargo, 'Cargo Atualizado')
    
    def test_editar_supervisor_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios na edição - CA3"""
        self.client.login(username='admin@test.com', password='senha123')
        
        dados = {
            'nome': '',
            'contato': '',
            'cargo': '',
            'empresa': ''
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Nome é obrigatório' in str(m) for m in messages_list))
        self.assertTrue(any('Cargo é obrigatório' in str(m) for m in messages_list))
        self.assertTrue(any('Empresa é obrigatória' in str(m) for m in messages_list))
    
    def test_editar_supervisor_trocar_empresa(self):
        """Testa troca de empresa do supervisor"""
        self.client.login(username='admin@test.com', password='senha123')
        
        # Criar nova empresa
        nova_empresa = Empresa.objects.create(
            cnpj="98765432109876",
            razao_social="Nova Empresa",
            rua="Nova Rua",
            numero=200,
            bairro="Novo Bairro"
        )
        
        dados = {
            'nome': 'Nome Mantido',
            'contato': '11999999999',
            'cargo': 'Cargo Mantido',
            'empresa': str(nova_empresa.id)
        }
        
        response = self.client.post(self.url, dados)
        
        self.assertEqual(response.status_code, 302)
        
        self.supervisor.refresh_from_db()
        self.assertEqual(self.supervisor.empresa.id, nova_empresa.id)


class IntegracaoEmpresaSupervisorTest(TestCase):
    """Testes de integração entre empresa e supervisor"""
    
    def setUp(self):
        self.client = Client()
        self.usuario_admin = Usuario.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='senha123',
            tipo='admin'
        )
    
    def test_fluxo_completo_cadastro_empresa_e_supervisor(self):
        """Testa fluxo completo: cadastrar empresa e depois supervisor vinculado"""
        self.client.login(username='admin@test.com', password='senha123')
        
        # Passo 1: Cadastrar empresa
        dados_empresa = {
            'cnpj': '12345678901234',
            'razao_social': 'Tech Company',
            'rua': 'Av Principal',
            'numero': '1000',
            'bairro': 'Centro'
        }
        
        response = self.client.post(reverse('cadastrar_empresa'), dados_empresa)
        self.assertEqual(response.status_code, 302)
        
        empresa = Empresa.objects.get(cnpj='12345678901234')
        
        # Passo 2: Cadastrar supervisor vinculado à empresa
        dados_supervisor = {
            'nome': 'Maria Supervisora',
            'contato': '11977776666',
            'cargo': 'Diretora de RH',
            'empresa': str(empresa.id),
            'email': 'maria@techcompany.com',
            'senha': 'senhasegura123'
        }
        
        response = self.client.post(reverse('cadastrar_supervisor'), dados_supervisor)
        self.assertEqual(response.status_code, 302)
        
        # Verificar vínculo correto
        supervisor = Supervisor.objects.get(nome='Maria Supervisora')
        self.assertEqual(supervisor.empresa.razao_social, 'Tech Company')
        self.assertEqual(supervisor.empresa.cnpj, '12345678901234')
    
    def test_visualizar_empresa_lista_supervisores(self):
        """Testa que ao visualizar empresa, lista seus supervisores"""
        self.client.login(username='admin@test.com', password='senha123')
        
        # Criar empresa
        empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa com Supervisores",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        # Criar supervisores vinculados
        for i in range(3):
            usuario = Usuario.objects.create_user(
                username=f'supervisor{i}@test.com',
                email=f'supervisor{i}@test.com',
                password='senha123',
                tipo='supervisor'
            )
            Supervisor.objects.create(
                nome=f'Supervisor {i}',
                contato=f'1199999000{i}',
                cargo='Gerente',
                empresa=empresa,
                usuario=usuario
            )
        
        response = self.client.get(reverse('visualizar_empresa', args=[empresa.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('supervisores', response.context)
        self.assertEqual(response.context['supervisores'].count(), 3)


# ==================== TESTES DE FORMULÁRIOS ====================

class EmpresaFormTest(TestCase):
    """Testes para o formulário EmpresaForm"""
    
    def test_form_valido(self):
        """Testa formulário com dados válidos"""
        from admin.forms import EmpresaForm
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Empresa Teste',
            'rua': 'Rua Teste',
            'numero': 100,
            'bairro': 'Centro'
        }
        
        form = EmpresaForm(data=dados)
        self.assertTrue(form.is_valid())
    
    def test_form_cnpj_invalido(self):
        """Testa formulário com CNPJ inválido"""
        from admin.forms import EmpresaForm
        
        dados = {
            'cnpj': '123',  # CNPJ curto
            'razao_social': 'Empresa Teste',
            'rua': 'Rua Teste',
            'numero': 100,
            'bairro': 'Centro'
        }
        
        form = EmpresaForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('cnpj', form.errors)
    
    def test_form_cnpj_duplicado(self):
        """Testa formulário com CNPJ duplicado"""
        from admin.forms import EmpresaForm
        
        # Criar empresa existente
        Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Existente",
            rua="Rua Existente",
            numero=100,
            bairro="Centro"
        )
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Nova Empresa',
            'rua': 'Nova Rua',
            'numero': 200,
            'bairro': 'Novo Bairro'
        }
        
        form = EmpresaForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('cnpj', form.errors)
    
    def test_form_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios"""
        from admin.forms import EmpresaForm
        
        form = EmpresaForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('cnpj', form.errors)
        self.assertIn('razao_social', form.errors)
        self.assertIn('rua', form.errors)
        self.assertIn('numero', form.errors)
        self.assertIn('bairro', form.errors)
    
    def test_form_numero_negativo(self):
        """Testa formulário com número negativo"""
        from admin.forms import EmpresaForm
        
        dados = {
            'cnpj': '12345678901234',
            'razao_social': 'Empresa Teste',
            'rua': 'Rua Teste',
            'numero': -10,
            'bairro': 'Centro'
        }
        
        form = EmpresaForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('numero', form.errors)
    
    def test_form_edicao_cnpj_duplicado_permite_mesmo(self):
        """Testa que na edição permite manter o mesmo CNPJ"""
        from admin.forms import EmpresaForm
        
        empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Original",
            rua="Rua Original",
            numero=100,
            bairro="Centro"
        )
        
        dados = {
            'cnpj': '12345678901234',  # Mesmo CNPJ
            'razao_social': 'Empresa Atualizada',
            'rua': 'Rua Atualizada',
            'numero': 200,
            'bairro': 'Novo Bairro'
        }
        
        form = EmpresaForm(data=dados, instance=empresa)
        self.assertTrue(form.is_valid())


class SupervisorFormTest(TestCase):
    """Testes para o formulário SupervisorForm"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
    
    def test_form_valido(self):
        """Testa formulário com dados válidos"""
        from admin.forms import SupervisorForm
        
        dados = {
            'nome': 'João Supervisor',
            'contato': '11999999999',
            'cargo': 'Gerente',
            'empresa': self.empresa.id,
            'email': 'joao@empresa.com',
            'senha': 'senha123456'
        }
        
        form = SupervisorForm(data=dados)
        self.assertTrue(form.is_valid())
    
    def test_form_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios"""
        from admin.forms import SupervisorForm
        
        form = SupervisorForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
        self.assertIn('cargo', form.errors)
        self.assertIn('empresa', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('senha', form.errors)
    
    def test_form_email_duplicado(self):
        """Testa formulário com email duplicado"""
        from admin.forms import SupervisorForm
        
        Usuario.objects.create_user(
            username='existente@empresa.com',
            email='existente@empresa.com',
            password='senha123',
            tipo='supervisor'
        )
        
        dados = {
            'nome': 'Novo Supervisor',
            'contato': '11999999999',
            'cargo': 'Gerente',
            'empresa': self.empresa.id,
            'email': 'existente@empresa.com',
            'senha': 'senha123456'
        }
        
        form = SupervisorForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_form_senha_curta(self):
        """Testa formulário com senha curta"""
        from admin.forms import SupervisorForm
        
        dados = {
            'nome': 'João Supervisor',
            'contato': '11999999999',
            'cargo': 'Gerente',
            'empresa': self.empresa.id,
            'email': 'joao@empresa.com',
            'senha': '12345'  # Menos de 6 caracteres
        }
        
        form = SupervisorForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('senha', form.errors)
    
    def test_form_cria_usuario_ao_salvar(self):
        """Testa que o formulário cria usuário ao salvar"""
        from admin.forms import SupervisorForm
        
        dados = {
            'nome': 'Novo Supervisor',
            'contato': '11999999999',
            'cargo': 'Diretor',
            'empresa': self.empresa.id,
            'email': 'novo@empresa.com',
            'senha': 'senha123456'
        }
        
        form = SupervisorForm(data=dados)
        self.assertTrue(form.is_valid())
        
        supervisor = form.save()
        
        self.assertIsNotNone(supervisor.usuario)
        self.assertEqual(supervisor.usuario.email, 'novo@empresa.com')
        self.assertEqual(supervisor.usuario.tipo, 'supervisor')


class SupervisorEditFormTest(TestCase):
    """Testes para o formulário SupervisorEditForm"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        self.usuario = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Original',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario
        )
    
    def test_form_edicao_valido(self):
        """Testa formulário de edição com dados válidos"""
        from admin.forms import SupervisorEditForm
        
        dados = {
            'nome': 'Supervisor Atualizado',
            'contato': '11888888888',
            'cargo': 'Diretor',
            'empresa': self.empresa.id
        }
        
        form = SupervisorEditForm(data=dados, instance=self.supervisor)
        self.assertTrue(form.is_valid())
    
    def test_form_edicao_sem_email_senha(self):
        """Testa que formulário de edição não tem campos email e senha"""
        from admin.forms import SupervisorEditForm
        
        form = SupervisorEditForm()
        self.assertNotIn('email', form.fields)
        self.assertNotIn('senha', form.fields)
    
    def test_form_edicao_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios na edição"""
        from admin.forms import SupervisorEditForm
        
        form = SupervisorEditForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
        self.assertIn('cargo', form.errors)
        self.assertIn('empresa', form.errors)


# ==================== TESTES DE ATIVIDADES ====================

class AtividadeModelTest(TestCase):
    """Testes para o modelo Atividade"""
    
    def setUp(self):
        # Criar dados de teste
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
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
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="11988888888",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_criar_atividade(self):
        """Testa criação de atividade"""
        from estagio.models import Atividade
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Desenvolvimento de API",
            descricao="Desenvolvimento de API REST para integração",
            data_realizacao=date.today(),
            horas_dedicadas=4
        )
        
        self.assertIsNotNone(atividade.id)
        self.assertEqual(atividade.status, 'pendente')
        self.assertIsNone(atividade.confirmado_por)
        self.assertIsNone(atividade.data_confirmacao)
    
    def test_confirmar_atividade(self):
        """Testa confirmação de atividade - CA2, CA4"""
        from estagio.models import Atividade, AtividadeHistorico
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Desenvolvimento de API",
            descricao="Desenvolvimento de API REST",
            data_realizacao=date.today(),
            horas_dedicadas=4
        )
        
        # Confirma a atividade
        atividade.confirmar(self.supervisor)
        
        # Verifica atualização de status (CA4)
        self.assertEqual(atividade.status, 'confirmada')
        
        # Verifica registro de data (CA2)
        self.assertIsNotNone(atividade.data_confirmacao)
        self.assertEqual(atividade.confirmado_por, self.supervisor)
        
        # Verifica histórico (CA5)
        historico = AtividadeHistorico.objects.filter(atividade=atividade)
        self.assertEqual(historico.count(), 1)
        self.assertEqual(historico.first().acao, 'confirmada')
    
    def test_rejeitar_atividade(self):
        """Testa rejeição de atividade com justificativa - CA3, CA4"""
        from estagio.models import Atividade, AtividadeHistorico
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade para Rejeitar",
            descricao="Descrição da atividade",
            data_realizacao=date.today(),
            horas_dedicadas=2
        )
        
        justificativa = "Atividade não corresponde ao escopo do estágio"
        
        # Rejeita a atividade
        atividade.rejeitar(self.supervisor, justificativa)
        
        # Verifica atualização de status (CA4)
        self.assertEqual(atividade.status, 'rejeitada')
        
        # Verifica justificativa (CA3)
        self.assertEqual(atividade.justificativa_rejeicao, justificativa)
        self.assertIsNotNone(atividade.data_confirmacao)
        
        # Verifica histórico (CA5)
        historico = AtividadeHistorico.objects.filter(atividade=atividade)
        self.assertEqual(historico.count(), 1)
        self.assertEqual(historico.first().acao, 'rejeitada')
        self.assertEqual(historico.first().observacoes, justificativa)


class ListarAtividadesPendentesViewTest(TestCase):
    """Testes para a view listar_atividades_pendentes - CA1"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
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
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="11988888888",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
        
        self.url = reverse('supervisor:atividades_pendentes')
    
    def test_listar_atividades_requer_login(self):
        """Testa que a listagem requer autenticação"""
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])
    
    def test_listar_atividades_pendentes_ca1(self):
        """Testa listagem de atividades pendentes - CA1"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        # Criar atividades de teste
        Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade 1",
            descricao="Descrição 1",
            data_realizacao=date.today(),
            horas_dedicadas=2,
            status='pendente'
        )
        
        Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade 2",
            descricao="Descrição 2",
            data_realizacao=date.today(),
            horas_dedicadas=3,
            status='pendente'
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('atividades', response.context)
        self.assertEqual(response.context['atividades'].count(), 2)
        self.assertIn('stats', response.context)
        self.assertEqual(response.context['stats']['pendentes'], 2)
    
    def test_filtrar_por_status(self):
        """Testa filtro de atividades por status"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade Pendente",
            descricao="Descrição",
            data_realizacao=date.today(),
            horas_dedicadas=2,
            status='pendente'
        )
        
        Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade Confirmada",
            descricao="Descrição",
            data_realizacao=date.today(),
            horas_dedicadas=3,
            status='confirmada'
        )
        
        # Filtrar por status confirmada
        response = self.client.get(self.url, {'status': 'confirmada'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['atividades'].count(), 1)
        self.assertEqual(response.context['atividades'].first().titulo, "Atividade Confirmada")
    
    def test_estatisticas_atividades(self):
        """Testa cálculo de estatísticas de atividades"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        # Criar atividades com diferentes status
        Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Pendente 1",
            descricao="Desc",
            data_realizacao=date.today(),
            horas_dedicadas=2,
            status='pendente'
        )
        
        Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Confirmada 1",
            descricao="Desc",
            data_realizacao=date.today(),
            horas_dedicadas=2,
            status='confirmada'
        )
        
        Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Rejeitada 1",
            descricao="Desc",
            data_realizacao=date.today(),
            horas_dedicadas=2,
            status='rejeitada'
        )
        
        response = self.client.get(self.url, {'status': ''})  # Sem filtro
        
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        self.assertEqual(stats['pendentes'], 1)
        self.assertEqual(stats['confirmadas'], 1)
        self.assertEqual(stats['rejeitadas'], 1)
        self.assertEqual(stats['total'], 3)


class ConfirmarAtividadeViewTest(TestCase):
    """Testes para a view confirmar_atividade - CA2, CA4"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
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
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="11988888888",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    @patch('admin.views.enviar_notificacao_email')
    def test_confirmar_atividade_ca2_ca4(self, mock_email):
        """Testa confirmação de atividade com registro de data - CA2, CA4"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade para Confirmar",
            descricao="Descrição da atividade",
            data_realizacao=date.today(),
            horas_dedicadas=4,
            status='pendente'
        )
        
        url = reverse('supervisor:confirmar_atividade', args=[atividade.id])
        response = self.client.post(url)
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica atualização de status (CA4)
        atividade.refresh_from_db()
        self.assertEqual(atividade.status, 'confirmada')
        
        # Verifica registro de data (CA2)
        self.assertIsNotNone(atividade.data_confirmacao)
        self.assertEqual(atividade.confirmado_por, self.supervisor)
        
        # Verifica email enviado
        mock_email.assert_called_once()
    
    def test_confirmar_atividade_get_redireciona(self):
        """Testa que GET redireciona para listagem"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade",
            descricao="Desc",
            data_realizacao=date.today(),
            horas_dedicadas=2,
            status='pendente'
        )
        
        url = reverse('supervisor:confirmar_atividade', args=[atividade.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
    
    @patch('admin.views.enviar_notificacao_email')
    def test_confirmar_atividade_ja_confirmada(self, mock_email):
        """Testa que não pode confirmar atividade já confirmada"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade Já Confirmada",
            descricao="Descrição",
            data_realizacao=date.today(),
            horas_dedicadas=4,
            status='confirmada'  # Já confirmada
        )
        
        url = reverse('supervisor:confirmar_atividade', args=[atividade.id])
        response = self.client.post(url)
        
        # Deve retornar 404 pois filtro só pega pendentes
        self.assertEqual(response.status_code, 404)


class RejeitarAtividadeViewTest(TestCase):
    """Testes para a view rejeitar_atividade - CA3, CA4"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
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
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="11988888888",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    @patch('admin.views.enviar_notificacao_email')
    def test_rejeitar_atividade_com_justificativa_ca3(self, mock_email):
        """Testa rejeição de atividade com justificativa obrigatória - CA3"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade para Rejeitar",
            descricao="Descrição da atividade",
            data_realizacao=date.today(),
            horas_dedicadas=4,
            status='pendente'
        )
        
        url = reverse('supervisor:rejeitar_atividade', args=[atividade.id])
        justificativa = "A atividade não corresponde ao plano de estágio definido"
        
        response = self.client.post(url, {'justificativa': justificativa})
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica atualização de status (CA4)
        atividade.refresh_from_db()
        self.assertEqual(atividade.status, 'rejeitada')
        
        # Verifica justificativa registrada (CA3)
        self.assertEqual(atividade.justificativa_rejeicao, justificativa)
        
        # Verifica email enviado com justificativa
        mock_email.assert_called_once()
    
    def test_rejeitar_atividade_sem_justificativa_ca3(self):
        """Testa que rejeição sem justificativa é bloqueada - CA3"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade Sem Justificativa",
            descricao="Descrição",
            data_realizacao=date.today(),
            horas_dedicadas=4,
            status='pendente'
        )
        
        url = reverse('supervisor:rejeitar_atividade', args=[atividade.id])
        
        # Tenta rejeitar sem justificativa
        response = self.client.post(url, {'justificativa': ''})
        
        # Deve redirecionar com erro
        self.assertEqual(response.status_code, 302)
        
        # Atividade deve permanecer pendente
        atividade.refresh_from_db()
        self.assertEqual(atividade.status, 'pendente')
    
    def test_rejeitar_atividade_justificativa_curta_ca3(self):
        """Testa que justificativa muito curta é bloqueada - CA3"""
        from estagio.models import Atividade
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade Justificativa Curta",
            descricao="Descrição",
            data_realizacao=date.today(),
            horas_dedicadas=4,
            status='pendente'
        )
        
        url = reverse('supervisor:rejeitar_atividade', args=[atividade.id])
        
        # Justificativa com menos de 10 caracteres
        response = self.client.post(url, {'justificativa': 'curta'})
        
        # Deve redirecionar com erro
        self.assertEqual(response.status_code, 302)
        
        # Atividade deve permanecer pendente
        atividade.refresh_from_db()
        self.assertEqual(atividade.status, 'pendente')


class HistoricoAtividadeViewTest(TestCase):
    """Testes para a view historico_atividade - CA5"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
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
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="11988888888",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_visualizar_historico_ca5(self):
        """Testa visualização do histórico de confirmações - CA5"""
        from estagio.models import Atividade, AtividadeHistorico
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade com Histórico",
            descricao="Descrição",
            data_realizacao=date.today(),
            horas_dedicadas=4,
            status='pendente'
        )
        
        # Registra histórico de criação
        AtividadeHistorico.objects.create(
            atividade=atividade,
            acao='registrada',
            supervisor=None,
            observacoes=None
        )
        
        # Confirma a atividade (cria entrada no histórico)
        atividade.confirmar(self.supervisor)
        
        url = reverse('supervisor:historico_atividade', args=[atividade.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('historico', response.context)
        # Deve ter 2 entradas: registrada + confirmada
        self.assertEqual(response.context['historico'].count(), 2)
    
    def test_historico_registra_rejeicao_ca5(self):
        """Testa que histórico registra rejeições - CA5"""
        from estagio.models import Atividade, AtividadeHistorico
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        atividade = Atividade.objects.create(
            aluno=self.aluno,
            estagio=self.estagio,
            titulo="Atividade Rejeitada",
            descricao="Descrição",
            data_realizacao=date.today(),
            horas_dedicadas=4,
            status='pendente'
        )
        
        # Rejeita a atividade
        justificativa = "Motivo da rejeição detalhado"
        atividade.rejeitar(self.supervisor, justificativa)
        
        url = reverse('supervisor:historico_atividade', args=[atividade.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica histórico
        historico = response.context['historico']
        self.assertEqual(historico.count(), 1)
        self.assertEqual(historico.first().acao, 'rejeitada')
        self.assertEqual(historico.first().observacoes, justificativa)


class AtividadeFormTest(TestCase):
    """Testes para o formulário AtividadeForm"""
    
    def test_form_valido(self):
        """Testa formulário com dados válidos"""
        from estagio.forms import AtividadeForm
        
        dados = {
            'titulo': 'Desenvolvimento de Feature',
            'descricao': 'Desenvolvimento de nova funcionalidade no sistema',
            'data_realizacao': date.today(),
            'horas_dedicadas': 4
        }
        
        form = AtividadeForm(data=dados)
        self.assertTrue(form.is_valid())
    
    def test_form_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios"""
        from estagio.forms import AtividadeForm
        
        form = AtividadeForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('titulo', form.errors)
        self.assertIn('descricao', form.errors)
        self.assertIn('data_realizacao', form.errors)
        self.assertIn('horas_dedicadas', form.errors)
    
    def test_form_data_futura(self):
        """Testa que data futura é rejeitada"""
        from estagio.forms import AtividadeForm
        
        dados = {
            'titulo': 'Atividade Futura',
            'descricao': 'Descrição',
            'data_realizacao': date.today() + timedelta(days=1),
            'horas_dedicadas': 4
        }
        
        form = AtividadeForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('data_realizacao', form.errors)
    
    def test_form_horas_negativas(self):
        """Testa que horas negativas são rejeitadas"""
        from estagio.forms import AtividadeForm
        
        dados = {
            'titulo': 'Atividade',
            'descricao': 'Descrição',
            'data_realizacao': date.today(),
            'horas_dedicadas': -5
        }
        
        form = AtividadeForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('horas_dedicadas', form.errors)
    
    def test_form_horas_excedentes(self):
        """Testa que mais de 24 horas são rejeitadas"""
        from estagio.forms import AtividadeForm
        
        dados = {
            'titulo': 'Atividade',
            'descricao': 'Descrição',
            'data_realizacao': date.today(),
            'horas_dedicadas': 25
        }
        
        form = AtividadeForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('horas_dedicadas', form.errors)


class RejeicaoAtividadeFormTest(TestCase):
    """Testes para o formulário RejeicaoAtividadeForm - CA3"""
    
    def test_form_valido(self):
        """Testa formulário com justificativa válida"""
        from estagio.forms import RejeicaoAtividadeForm
        
        dados = {
            'justificativa': 'A atividade não corresponde ao escopo definido no plano de estágio.'
        }
        
        form = RejeicaoAtividadeForm(data=dados)
        self.assertTrue(form.is_valid())
    
    def test_form_justificativa_obrigatoria(self):
        """Testa que justificativa é obrigatória - CA3"""
        from estagio.forms import RejeicaoAtividadeForm
        
        form = RejeicaoAtividadeForm(data={'justificativa': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('justificativa', form.errors)
    
    def test_form_justificativa_minima(self):
        """Testa que justificativa deve ter pelo menos 10 caracteres - CA3"""
        from estagio.forms import RejeicaoAtividadeForm
        
        dados = {
            'justificativa': 'curta'  # Menos de 10 caracteres
        }
        
        form = RejeicaoAtividadeForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('justificativa', form.errors)


# ==================== TESTES DE VÍNCULO ALUNO-VAGA ====================

class VinculoHistoricoModelTest(TestCase):
    """Testes para o modelo VinculoHistorico - CA8"""
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
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
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        # Cria vaga aprovada e disponível
        self.vaga = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='disponivel'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=None  # Sem vínculo
        )
    
    def test_vincular_aluno_registra_historico_ca8(self):
        """Testa que vincular aluno registra no histórico - CA8"""
        from estagio.models import VinculoHistorico
        
        # Vincula o aluno à vaga
        self.vaga.vincular_aluno(self.aluno, realizado_por=self.usuario_coordenador)
        
        # Verifica se o histórico foi criado
        historico = VinculoHistorico.objects.filter(aluno=self.aluno, estagio=self.vaga)
        self.assertEqual(historico.count(), 1)
        self.assertEqual(historico.first().acao, 'vinculado')
        self.assertEqual(historico.first().realizado_por, self.usuario_coordenador)
    
    def test_desvincular_aluno_registra_historico_ca8(self):
        """Testa que desvincular aluno registra no histórico - CA8"""
        from estagio.models import VinculoHistorico
        
        # Primeiro vincula
        self.vaga.vincular_aluno(self.aluno, realizado_por=self.usuario_coordenador)
        
        # Depois desvincula
        self.vaga.desvincular_aluno(
            self.aluno, 
            realizado_por=self.usuario_coordenador,
            observacoes="Desistência do aluno"
        )
        
        # Verifica se o histórico tem 2 entradas
        historico = VinculoHistorico.objects.filter(aluno=self.aluno, estagio=self.vaga)
        self.assertEqual(historico.count(), 2)
        
        # Verifica a última ação
        ultimo = historico.order_by('-data_hora').first()
        self.assertEqual(ultimo.acao, 'desvinculado')
        self.assertEqual(ultimo.observacoes, "Desistência do aluno")
    
    def test_vincular_atualiza_status_vaga_ca7(self):
        """Testa que vincular aluno atualiza status da vaga - CA7"""
        self.assertEqual(self.vaga.status_vaga, 'disponivel')
        
        # Vincula o aluno
        self.vaga.vincular_aluno(self.aluno, realizado_por=self.usuario_coordenador)
        
        # Verifica atualização
        self.vaga.refresh_from_db()
        self.assertEqual(self.vaga.status_vaga, 'ocupada')
    
    def test_desvincular_atualiza_status_vaga(self):
        """Testa que desvincular aluno retorna status da vaga para disponível"""
        # Vincula o aluno
        self.vaga.vincular_aluno(self.aluno, realizado_por=self.usuario_coordenador)
        self.assertEqual(self.vaga.status_vaga, 'ocupada')
        
        # Desvincula o aluno
        self.vaga.desvincular_aluno(self.aluno, realizado_por=self.usuario_coordenador)
        
        # Verifica atualização
        self.vaga.refresh_from_db()
        self.assertEqual(self.vaga.status_vaga, 'disponivel')


class EstagioVagaModelTest(TestCase):
    """Testes para os métodos de vaga no modelo Estagio"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
    
    def test_is_disponivel_vaga_aprovada_disponivel(self):
        """Testa que vaga aprovada e disponível retorna True"""
        vaga = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='disponivel'
        )
        
        self.assertTrue(vaga.is_disponivel())
    
    def test_is_disponivel_vaga_nao_aprovada(self):
        """Testa que vaga não aprovada não está disponível - CA4"""
        vaga = Estagio.objects.create(
            titulo="Estágio em Análise",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='analise',
            status_vaga='disponivel'
        )
        
        self.assertFalse(vaga.is_disponivel())
    
    def test_is_disponivel_vaga_ocupada(self):
        """Testa que vaga ocupada não está disponível - CA4"""
        vaga = Estagio.objects.create(
            titulo="Estágio Ocupado",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='ocupada'
        )
        
        self.assertFalse(vaga.is_disponivel())


class ListarVagasDisponiveisViewTest(TestCase):
    """Testes para a view listar_vagas_disponiveis - CA4"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.coordenador = CursoCoordenador.objects.create(
            nome='Coordenador Teste',
            contato='coordenador@test.com',
            curso='Sistemas de Informação',
            usuario=self.usuario_coordenador
        )
        
        self.url = reverse('coordenador:listar_vagas_disponiveis')
    
    def test_listar_vagas_requer_login(self):
        """Testa que listagem requer autenticação"""
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])
    
    def test_listar_apenas_vagas_disponiveis_ca4(self):
        """Testa que lista apenas vagas disponíveis - CA4"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        # Cria vaga disponível
        Estagio.objects.create(
            titulo="Vaga Disponível",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='disponivel'
        )
        
        # Cria vaga ocupada (não deve aparecer)
        Estagio.objects.create(
            titulo="Vaga Ocupada",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='ocupada'
        )
        
        # Cria vaga em análise (não deve aparecer)
        Estagio.objects.create(
            titulo="Vaga Em Análise",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='analise',
            status_vaga='disponivel'
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('vagas', response.context)
        # Apenas a vaga disponível e aprovada
        self.assertEqual(response.context['vagas'].count(), 1)
        self.assertEqual(response.context['vagas'].first().titulo, "Vaga Disponível")


class VincularAlunoVagaViewTest(TestCase):
    """Testes para a view vincular_aluno_vaga - CA5, CA6, CA7"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.usuario_aluno2 = Usuario.objects.create_user(
            username='aluno2@test.com',
            email='aluno2@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.coordenador = CursoCoordenador.objects.create(
            nome='Coordenador Teste',
            contato='coordenador@test.com',
            curso='Sistemas de Informação',
            usuario=self.usuario_coordenador
        )
        
        self.vaga = Estagio.objects.create(
            titulo="Vaga Disponível",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='disponivel'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=None
        )
        
        self.aluno2 = Aluno.objects.create(
            nome="Aluno 2",
            contato="aluno2@test.com",
            matricula="12345678902",
            usuario=self.usuario_aluno2,
            instituicao=self.instituicao,
            estagio=None
        )
        
        self.url = reverse('coordenador:vincular_aluno_vaga')
    
    @patch('admin.views.enviar_notificacao_email')
    def test_vincular_aluno_vaga_sucesso(self, mock_email):
        """Testa vínculo bem-sucedido entre aluno e vaga"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.post(self.url, {
            'aluno': self.aluno.id,
            'vaga': self.vaga.id,
            'observacoes': ''
        })
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica vínculo criado
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.estagio, self.vaga)
        
        # Verifica status da vaga atualizado - CA7
        self.vaga.refresh_from_db()
        self.assertEqual(self.vaga.status_vaga, 'ocupada')
    
    def test_impedir_vinculo_aluno_com_vaga_ativa_ca5(self):
        """Testa que aluno com vaga ativa não pode ter outra - CA5"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        # Vincula aluno à vaga
        self.aluno.estagio = self.vaga
        self.aluno.save()
        self.vaga.status_vaga = 'ocupada'
        self.vaga.save()
        
        # Cria outra vaga
        vaga2 = Estagio.objects.create(
            titulo="Outra Vaga",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='disponivel'
        )
        
        # Tenta vincular novamente
        response = self.client.post(self.url, {
            'aluno': self.aluno.id,
            'vaga': vaga2.id,
            'observacoes': ''
        })
        
        # Verifica que não vinculou
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.estagio, self.vaga)  # Continua com a vaga original
    
    @patch('admin.views.enviar_notificacao_email')
    def test_registrar_historico_vinculo_ca8(self, mock_email):
        """Testa que o histórico é registrado ao vincular - CA8"""
        from estagio.models import VinculoHistorico
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.post(self.url, {
            'aluno': self.aluno.id,
            'vaga': self.vaga.id,
            'observacoes': ''
        })
        
        # Verifica histórico criado
        historico = VinculoHistorico.objects.filter(
            aluno=self.aluno,
            estagio=self.vaga
        )
        self.assertEqual(historico.count(), 1)
        self.assertEqual(historico.first().acao, 'vinculado')


class VinculoAlunoVagaFormTest(TestCase):
    """Testes para o formulário VinculoAlunoVagaForm - CA5, CA6"""
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.vaga = Estagio.objects.create(
            titulo="Vaga Disponível",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='disponivel'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=None
        )
    
    def test_form_valido(self):
        """Testa formulário com dados válidos"""
        from estagio.forms import VinculoAlunoVagaForm
        
        form = VinculoAlunoVagaForm(data={
            'aluno': self.aluno.id,
            'vaga': self.vaga.id,
            'observacoes': ''
        })
        
        self.assertTrue(form.is_valid())
    
    def test_form_rejeita_aluno_com_vaga_ativa_ca5(self):
        """Testa que formulário rejeita aluno com vaga ativa - CA5"""
        from estagio.forms import VinculoAlunoVagaForm
        
        # Vincula aluno à vaga
        self.aluno.estagio = self.vaga
        self.aluno.save()
        
        # Cria outra vaga
        vaga2 = Estagio.objects.create(
            titulo="Outra Vaga",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='disponivel'
        )
        
        form = VinculoAlunoVagaForm(data={
            'aluno': self.aluno.id,
            'vaga': vaga2.id,
            'observacoes': ''
        })
        
        # Aluno com vaga ativa não deve aparecer na lista
        self.assertNotIn(self.aluno, form.fields['aluno'].queryset)
    
    def test_form_mostra_apenas_vagas_disponiveis_ca4(self):
        """Testa que formulário mostra apenas vagas disponíveis - CA4"""
        from estagio.forms import VinculoAlunoVagaForm
        
        # Cria vaga ocupada
        vaga_ocupada = Estagio.objects.create(
            titulo="Vaga Ocupada",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='ocupada'
        )
        
        form = VinculoAlunoVagaForm()
        
        # Vaga disponível deve estar na lista
        self.assertIn(self.vaga, form.fields['vaga'].queryset)
        
        # Vaga ocupada não deve estar na lista
        self.assertNotIn(vaga_ocupada, form.fields['vaga'].queryset)
    
    def test_form_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios"""
        from estagio.forms import VinculoAlunoVagaForm
        
        form = VinculoAlunoVagaForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('aluno', form.errors)
        self.assertIn('vaga', form.errors)


class HistoricoVinculoViewTest(TestCase):
    """Testes para as views de histórico de vínculo - CA8"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.coordenador = CursoCoordenador.objects.create(
            nome='Coordenador Teste',
            contato='coordenador@test.com',
            curso='Sistemas de Informação',
            usuario=self.usuario_coordenador
        )
        
        self.vaga = Estagio.objects.create(
            titulo="Vaga Teste",
            cargo="Dev",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='aprovado',
            status_vaga='disponivel'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=None
        )
    
    def test_visualizar_historico_aluno_ca8(self):
        """Testa visualização do histórico de vínculos do aluno - CA8"""
        from estagio.models import VinculoHistorico
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        # Cria histórico
        VinculoHistorico.objects.create(
            aluno=self.aluno,
            estagio=self.vaga,
            acao='vinculado',
            realizado_por=self.usuario_coordenador
        )
        
        url = reverse('coordenador:historico_vinculo_aluno', args=[self.aluno.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('historico', response.context)
        self.assertEqual(response.context['historico'].count(), 1)
    
    def test_visualizar_historico_vaga_ca8(self):
        """Testa visualização do histórico de vínculos da vaga - CA8"""
        from estagio.models import VinculoHistorico
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        # Cria histórico
        VinculoHistorico.objects.create(
            aluno=self.aluno,
            estagio=self.vaga,
            acao='vinculado',
            realizado_por=self.usuario_coordenador
        )
        
        url = reverse('coordenador:historico_vinculo_vaga', args=[self.vaga.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('historico', response.context)
        self.assertEqual(response.context['historico'].count(), 1)


# ==================== TESTES DE AVALIAÇÃO DE DESEMPENHO ====================

class CriterioAvaliacaoModelTest(TestCase):
    """Testes para o modelo CriterioAvaliacao - CA1"""
    
    def test_criar_criterio_avaliacao(self):
        """Testa criação de critério de avaliação - CA1"""
        from estagio.models import CriterioAvaliacao
        
        criterio = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            descricao='Avalia se o estagiário cumpre os horários',
            peso=1.5,
            nota_minima=0,
            nota_maxima=10,
            obrigatorio=True,
            ordem=1
        )
        
        self.assertEqual(criterio.nome, 'Pontualidade')
        self.assertEqual(criterio.peso, 1.5)
        self.assertTrue(criterio.obrigatorio)
    
    def test_criterio_str(self):
        """Testa representação string do critério"""
        from estagio.models import CriterioAvaliacao
        
        criterio = CriterioAvaliacao.objects.create(
            nome='Proatividade',
            obrigatorio=True
        )
        
        self.assertIn('Proatividade', str(criterio))
        self.assertIn('Obrigatório', str(criterio))


class AvaliacaoModelTest(TestCase):
    """Testes para o modelo Avaliacao - CA1, CA2, CA3"""
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_criar_avaliacao_por_periodo_ca2(self):
        """Testa criação de avaliação com período - CA2"""
        from estagio.models import Avaliacao
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        self.assertEqual(avaliacao.periodo, 'mensal')
        self.assertEqual(avaliacao.status, 'rascunho')
        self.assertIsNotNone(avaliacao.periodo_inicio)
        self.assertIsNotNone(avaliacao.periodo_fim)
    
    def test_avaliacao_is_completa_sem_criterios(self):
        """Testa que avaliação sem critérios obrigatórios está completa"""
        from estagio.models import Avaliacao
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        # Sem critérios obrigatórios, deve estar completa
        self.assertTrue(avaliacao.is_completa())
    
    def test_avaliacao_incompleta_sem_nota_obrigatoria_ca3(self):
        """Testa que avaliação está incompleta sem nota de critério obrigatório - CA3"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critério obrigatório
        criterio = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            obrigatorio=True
        )
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        # Cria nota sem valor
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=None
        )
        
        # Deve estar incompleta
        self.assertFalse(avaliacao.is_completa())
        self.assertEqual(avaliacao.get_criterios_faltantes().count(), 1)
    
    def test_avaliacao_completa_com_notas_ca3(self):
        """Testa que avaliação está completa com todas as notas - CA3"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critérios
        criterio1 = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            obrigatorio=True,
            peso=1.0
        )
        criterio2 = CriterioAvaliacao.objects.create(
            nome='Qualidade',
            obrigatorio=True,
            peso=2.0
        )
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        # Cria notas preenchidas
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio1,
            nota=8.0
        )
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio2,
            nota=9.0
        )
        
        # Deve estar completa
        self.assertTrue(avaliacao.is_completa())
        self.assertEqual(avaliacao.get_criterios_faltantes().count(), 0)
    
    def test_calcular_nota_media_ponderada(self):
        """Testa cálculo da nota média ponderada"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critérios com pesos diferentes
        criterio1 = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            peso=1.0
        )
        criterio2 = CriterioAvaliacao.objects.create(
            nome='Qualidade',
            peso=2.0
        )
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        # Notas: Pontualidade=6 (peso 1), Qualidade=9 (peso 2)
        # Média = (6*1 + 9*2) / (1+2) = 24/3 = 8.0
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio1,
            nota=6.0
        )
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio2,
            nota=9.0
        )
        
        media = avaliacao.calcular_nota_media()
        self.assertEqual(media, 8.0)
    
    def test_enviar_avaliacao_incompleta_falha_ca3(self):
        """Testa que envio de avaliação incompleta falha - CA3"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critério obrigatório
        criterio = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            obrigatorio=True
        )
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        # Não preenche a nota
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=None
        )
        
        # Deve lançar exceção
        with self.assertRaises(ValueError) as context:
            avaliacao.enviar()
        
        self.assertIn('incompleta', str(context.exception))
    
    def test_enviar_avaliacao_completa_sucesso(self):
        """Testa que envio de avaliação completa funciona"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critério obrigatório
        criterio = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            obrigatorio=True,
            peso=1.0
        )
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        # Preenche a nota
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=8.5
        )
        
        # Envia
        result = avaliacao.enviar()
        
        self.assertTrue(result)
        self.assertEqual(avaliacao.status, 'enviada')
        self.assertEqual(avaliacao.nota, 8.5)


class NotaCriterioModelTest(TestCase):
    """Testes para o modelo NotaCriterio"""
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_nota_dentro_limites(self):
        """Testa nota dentro dos limites do critério"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(
            nome='Teste',
            nota_minima=0,
            nota_maxima=10
        )
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        nota = NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=7.5
        )
        
        self.assertEqual(nota.nota, 7.5)
    
    def test_nota_fora_limites_validacao(self):
        """Testa validação de nota fora dos limites"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        from django.core.exceptions import ValidationError
        
        criterio = CriterioAvaliacao.objects.create(
            nome='Teste',
            nota_minima=0,
            nota_maxima=10
        )
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        nota = NotaCriterio(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=15.0  # Acima do máximo
        )
        
        with self.assertRaises(ValidationError):
            nota.clean()


class ListarAvaliacoesViewTest(TestCase):
    """Testes para a view listar_avaliacoes"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
        
        self.url = reverse('supervisor:listar_avaliacoes')
    
    def test_listar_avaliacoes_requer_login(self):
        """Testa que listagem requer autenticação"""
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])
    
    def test_listar_avaliacoes_supervisor(self):
        """Testa listagem de avaliações do supervisor"""
        from estagio.models import Avaliacao
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        # Cria avaliação
        Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('avaliacoes', response.context)
        self.assertEqual(response.context['avaliacoes'].count(), 1)


class CriarAvaliacaoViewTest(TestCase):
    """Testes para a view criar_avaliacao - CA1, CA2"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_criar_avaliacao_sucesso_ca2(self):
        """Testa criação de avaliação com período - CA2"""
        from estagio.models import Avaliacao, CriterioAvaliacao
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        # Cria critério
        CriterioAvaliacao.objects.create(nome='Pontualidade', obrigatorio=True)
        
        url = reverse('supervisor:criar_avaliacao', args=[self.aluno.id])
        
        response = self.client.post(url, {
            'periodo': 'mensal',
            'periodo_inicio': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'periodo_fim': date.today().strftime('%Y-%m-%d'),
            'parecer': ''
        })
        
        # Verifica redirecionamento para edição
        self.assertEqual(response.status_code, 302)
        
        # Verifica avaliação criada
        avaliacao = Avaliacao.objects.filter(aluno=self.aluno).first()
        self.assertIsNotNone(avaliacao)
        self.assertEqual(avaliacao.periodo, 'mensal')
        self.assertEqual(avaliacao.status, 'rascunho')


class EnviarAvaliacaoViewTest(TestCase):
    """Testes para a view enviar_avaliacao - CA3"""
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_enviar_avaliacao_incompleta_falha_ca3(self):
        """Testa que envio de avaliação incompleta é bloqueado - CA3"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        # Cria critério obrigatório
        criterio = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            obrigatorio=True
        )
        
        # Cria avaliação sem nota preenchida
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=None  # Não preenchida
        )
        
        url = reverse('supervisor:enviar_avaliacao', args=[avaliacao.id])
        response = self.client.post(url)
        
        # Deve redirecionar com erro
        self.assertEqual(response.status_code, 302)
        
        # Status não deve mudar
        avaliacao.refresh_from_db()
        self.assertNotEqual(avaliacao.status, 'enviada')
    
    @patch('admin.views.enviar_notificacao_email')
    def test_enviar_avaliacao_completa_sucesso(self, mock_email):
        """Testa envio de avaliação completa"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        self.client.login(username='supervisor@test.com', password='senha123')
        
        # Cria critério obrigatório
        criterio = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            obrigatorio=True,
            peso=1.0
        )
        
        # Cria avaliação com nota preenchida
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=8.5
        )
        
        url = reverse('supervisor:enviar_avaliacao', args=[avaliacao.id])
        response = self.client.post(url)
        
        # Deve redirecionar com sucesso
        self.assertEqual(response.status_code, 302)
        
        # Status deve mudar
        avaliacao.refresh_from_db()
        self.assertEqual(avaliacao.status, 'enviada')
        self.assertEqual(avaliacao.nota, 8.5)


class AvaliacaoFormTest(TestCase):
    """Testes para o formulário AvaliacaoForm - CA2"""
    
    def test_form_valido(self):
        """Testa formulário com dados válidos"""
        from estagio.forms import AvaliacaoForm
        
        dados = {
            'periodo': 'mensal',
            'periodo_inicio': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'periodo_fim': date.today().strftime('%Y-%m-%d'),
            'parecer': 'Bom desempenho no período.'
        }
        
        form = AvaliacaoForm(data=dados)
        self.assertTrue(form.is_valid())
    
    def test_form_periodo_inicio_futuro(self):
        """Testa que período início futuro é rejeitado"""
        from estagio.forms import AvaliacaoForm
        
        dados = {
            'periodo': 'mensal',
            'periodo_inicio': (date.today() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'periodo_fim': (date.today() + timedelta(days=35)).strftime('%Y-%m-%d'),
            'parecer': ''
        }
        
        form = AvaliacaoForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('periodo_inicio', form.errors)
    
    def test_form_periodo_fim_antes_inicio(self):
        """Testa que período fim antes do início é rejeitado"""
        from estagio.forms import AvaliacaoForm
        
        dados = {
            'periodo': 'mensal',
            'periodo_inicio': date.today().strftime('%Y-%m-%d'),
            'periodo_fim': (date.today() - timedelta(days=5)).strftime('%Y-%m-%d'),
            'parecer': ''
        }
        
        form = AvaliacaoForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('periodo_fim', form.errors)


class NotaCriterioFormTest(TestCase):
    """Testes para o formulário NotaCriterioForm - CA1, CA3"""
    
    def test_form_criterio_obrigatorio_sem_nota_ca3(self):
        """Testa que critério obrigatório sem nota é rejeitado - CA3"""
        from estagio.forms import NotaCriterioForm
        from estagio.models import CriterioAvaliacao
        
        criterio = CriterioAvaliacao(
            nome='Pontualidade',
            obrigatorio=True,
            nota_minima=0,
            nota_maxima=10
        )
        
        form = NotaCriterioForm(data={'nota': None}, criterio=criterio)
        self.assertFalse(form.is_valid())
        self.assertIn('nota', form.errors)
    
    def test_form_nota_dentro_limites(self):
        """Testa nota dentro dos limites do critério"""
        from estagio.forms import NotaCriterioForm
        from estagio.models import CriterioAvaliacao
        
        criterio = CriterioAvaliacao(
            nome='Pontualidade',
            obrigatorio=True,
            nota_minima=0,
            nota_maxima=10
        )
        
        form = NotaCriterioForm(data={'nota': 7.5}, criterio=criterio)
        self.assertTrue(form.is_valid())
    
    def test_form_nota_abaixo_minimo(self):
        """Testa que nota abaixo do mínimo é rejeitada"""
        from estagio.forms import NotaCriterioForm
        from estagio.models import CriterioAvaliacao
        
        criterio = CriterioAvaliacao(
            nome='Pontualidade',
            obrigatorio=False,
            nota_minima=0,
            nota_maxima=10
        )
        
        form = NotaCriterioForm(data={'nota': -1}, criterio=criterio)
        self.assertFalse(form.is_valid())
        self.assertIn('nota', form.errors)
    
    def test_form_nota_acima_maximo(self):
        """Testa que nota acima do máximo é rejeitada"""
        from estagio.forms import NotaCriterioForm
        from estagio.models import CriterioAvaliacao
        
        criterio = CriterioAvaliacao(
            nome='Pontualidade',
            obrigatorio=False,
            nota_minima=0,
            nota_maxima=10
        )
        
        form = NotaCriterioForm(data={'nota': 15}, criterio=criterio)
        self.assertFalse(form.is_valid())
        self.assertIn('nota', form.errors)


class AvaliacaoCompletaFormTest(TestCase):
    """Testes para o formulário AvaliacaoCompletaForm - CA3"""
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@test.com',
            email='supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Teste',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="aluno@test.com",
            matricula="12345678901",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_form_avaliacao_incompleta_ca3(self):
        """Testa que formulário rejeita avaliação incompleta - CA3"""
        from estagio.forms import AvaliacaoCompletaForm
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critério obrigatório
        criterio = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            obrigatorio=True
        )
        
        # Cria avaliação sem nota
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=None
        )
        
        form = AvaliacaoCompletaForm(
            data={'confirmar_envio': True},
            avaliacao=avaliacao
        )
        
        self.assertFalse(form.is_valid())
    
    def test_form_avaliacao_completa(self):
        """Testa que formulário aceita avaliação completa"""
        from estagio.forms import AvaliacaoCompletaForm
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critério obrigatório
        criterio = CriterioAvaliacao.objects.create(
            nome='Pontualidade',
            obrigatorio=True
        )
        
        # Cria avaliação com nota
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        NotaCriterio.objects.create(
            avaliacao=avaliacao,
            criterio=criterio,
            nota=8.0
        )
        
        form = AvaliacaoCompletaForm(
            data={'confirmar_envio': True},
            avaliacao=avaliacao
        )
        
        self.assertTrue(form.is_valid())


# ==================== TESTES DE PARECER FINAL - CA4, CA5, CA6 ====================

class CalculoNotaFinalTest(TestCase):
    """
    Testes para o cálculo automático da nota final - CA4
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901234",
            razao_social="Empresa Teste",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor_ca4@test.com',
            email='supervisor_ca4@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno_ca4@test.com',
            email='aluno_ca4@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor CA4',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio Teste CA4",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno CA4",
            contato="aluno_ca4@test.com",
            matricula="CA400000001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_calcular_nota_final_media_simples(self):
        """CA4 - Testa cálculo de nota final com pesos iguais"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critérios com mesmo peso
        criterio1 = CriterioAvaliacao.objects.create(nome='Critério 1', peso=1.0, obrigatorio=True)
        criterio2 = CriterioAvaliacao.objects.create(nome='Critério 2', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio1, nota=8.0)
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio2, nota=6.0)
        
        nota_final = avaliacao.calcular_nota_final()
        
        # Média esperada: (8.0 + 6.0) / 2 = 7.0
        self.assertEqual(nota_final, 7.0)
    
    def test_calcular_nota_final_media_ponderada(self):
        """CA4 - Testa cálculo de nota final com pesos diferentes"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        # Cria critérios com pesos diferentes
        criterio1 = CriterioAvaliacao.objects.create(nome='Critério Peso 2', peso=2.0, obrigatorio=True)
        criterio2 = CriterioAvaliacao.objects.create(nome='Critério Peso 1', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio1, nota=9.0)
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio2, nota=6.0)
        
        nota_final = avaliacao.calcular_nota_final()
        
        # Média ponderada: (9.0*2 + 6.0*1) / (2+1) = (18+6)/3 = 8.0
        self.assertEqual(nota_final, 8.0)
    
    def test_calcular_nota_final_sem_notas_erro(self):
        """CA4 - Testa que erro é levantado quando não há notas"""
        from estagio.models import Avaliacao
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        with self.assertRaises(ValueError) as context:
            avaliacao.calcular_nota_final()
        
        self.assertIn('notas suficientes', str(context.exception))


class ParecerObrigatorioTest(TestCase):
    """
    Testes para validação de parecer obrigatório - CA5
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901235",
            razao_social="Empresa Teste CA5",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor_ca5@test.com',
            email='supervisor_ca5@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno_ca5@test.com',
            email='aluno_ca5@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor CA5',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio Teste CA5",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno CA5",
            contato="aluno_ca5@test.com",
            matricula="CA500000001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_validar_parecer_vazio_erro(self):
        """CA5 - Testa que parecer vazio é rejeitado"""
        from estagio.models import Avaliacao
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        with self.assertRaises(ValueError) as context:
            avaliacao.validar_parecer_final('')
        
        self.assertIn('obrigatório', str(context.exception))
    
    def test_validar_parecer_muito_curto_erro(self):
        """CA5 - Testa que parecer com menos de 50 caracteres é rejeitado"""
        from estagio.models import Avaliacao
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        # Texto com menos de 50 caracteres
        parecer_curto = "Bom desempenho."
        
        with self.assertRaises(ValueError) as context:
            avaliacao.validar_parecer_final(parecer_curto)
        
        self.assertIn('50 caracteres', str(context.exception))
    
    def test_validar_parecer_valido(self):
        """CA5 - Testa que parecer com 50+ caracteres é aceito"""
        from estagio.models import Avaliacao
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today()
        )
        
        parecer_valido = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado."
        
        resultado = avaliacao.validar_parecer_final(parecer_valido)
        
        self.assertTrue(resultado)
    
    def test_form_parecer_final_vazio_erro(self):
        """CA5 - Testa que formulário rejeita parecer vazio"""
        from estagio.forms import ParecerFinalForm
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.0)
        
        form = ParecerFinalForm(
            data={
                'parecer_final': '',
                'disponibilizar_consulta': True,
                'confirmar_emissao': True
            },
            avaliacao=avaliacao
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('parecer_final', form.errors)
    
    def test_form_parecer_final_curto_erro(self):
        """CA5 - Testa que formulário rejeita parecer muito curto"""
        from estagio.forms import ParecerFinalForm
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.0)
        
        form = ParecerFinalForm(
            data={
                'parecer_final': 'Parecer curto',
                'disponibilizar_consulta': True,
                'confirmar_emissao': True
            },
            avaliacao=avaliacao
        )
        
        self.assertFalse(form.is_valid())


class EmitirParecerFinalTest(TestCase):
    """
    Testes para emissão do parecer final - CA4, CA5, CA6
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901236",
            razao_social="Empresa Teste Emitir",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor_emitir@test.com',
            email='supervisor_emitir@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno_emitir@test.com',
            email='aluno_emitir@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Emitir',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio Teste Emitir",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Emitir",
            contato="aluno_emitir@test.com",
            matricula="EMIT0000001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_emitir_parecer_final_sucesso(self):
        """CA4, CA5 - Testa emissão de parecer final com sucesso"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.5)
        
        parecer = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado, com destaque para a proatividade."
        
        nota_final, parecer_final = avaliacao.emitir_parecer_final(parecer)
        
        avaliacao.refresh_from_db()
        
        self.assertEqual(nota_final, 8.5)
        self.assertEqual(avaliacao.nota_final, 8.5)
        self.assertEqual(avaliacao.parecer_final, parecer.strip())
        self.assertEqual(avaliacao.status, 'parecer_emitido')
        self.assertIsNotNone(avaliacao.data_emissao_parecer)
    
    def test_emitir_parecer_disponibiliza_consulta(self):
        """CA6 - Testa que emitir parecer disponibiliza para consulta"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=7.5)
        
        parecer = "O estagiário demonstrou bom desempenho durante o período avaliado, cumprindo as expectativas estabelecidas."
        
        avaliacao.emitir_parecer_final(parecer, disponibilizar_consulta=True)
        
        avaliacao.refresh_from_db()
        
        self.assertTrue(avaliacao.parecer_disponivel_consulta)
    
    def test_emitir_parecer_sem_disponibilizar(self):
        """CA6 - Testa emissão sem disponibilizar para consulta"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=7.5)
        
        parecer = "O estagiário demonstrou bom desempenho durante o período avaliado, cumprindo as expectativas estabelecidas."
        
        avaliacao.emitir_parecer_final(parecer, disponibilizar_consulta=False)
        
        avaliacao.refresh_from_db()
        
        self.assertFalse(avaliacao.parecer_disponivel_consulta)
    
    def test_emitir_parecer_avaliacao_incompleta_erro(self):
        """CA4 - Testa que não pode emitir parecer para avaliação incompleta"""
        from estagio.models import Avaliacao, CriterioAvaliacao
        
        CriterioAvaliacao.objects.create(nome='Critério Obrigatório', obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='rascunho'
        )
        
        parecer = "Parecer de teste com mais de cinquenta caracteres para validar a regra do sistema."
        
        with self.assertRaises(ValueError) as context:
            avaliacao.emitir_parecer_final(parecer)
        
        self.assertIn('completa', str(context.exception).lower())
    
    def test_emitir_parecer_duplicado_erro(self):
        """CA5 - Testa que não pode emitir parecer duas vezes"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.0)
        
        parecer = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado."
        
        # Primeira emissão
        avaliacao.emitir_parecer_final(parecer)
        
        # Segunda tentativa deve falhar
        with self.assertRaises(ValueError) as context:
            avaliacao.emitir_parecer_final(parecer)
        
        self.assertIn('já foi emitido', str(context.exception))


class ConsultaParecerTest(TestCase):
    """
    Testes para consulta de parecer pelo aluno - CA6
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901237",
            razao_social="Empresa Teste Consulta",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor_consulta@test.com',
            email='supervisor_consulta@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno_consulta@test.com',
            email='aluno_consulta@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Consulta',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio Teste Consulta",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Consulta",
            contato="aluno_consulta@test.com",
            matricula="CONS0000001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_get_parecer_para_consulta_disponivel(self):
        """CA6 - Testa que parecer disponível retorna dados corretos"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        from django.utils import timezone
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=9.0)
        
        parecer_texto = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado."
        avaliacao.emitir_parecer_final(parecer_texto, disponibilizar_consulta=True)
        
        avaliacao.refresh_from_db()
        parecer_dados = avaliacao.get_parecer_para_consulta()
        
        self.assertIsNotNone(parecer_dados)
        self.assertEqual(parecer_dados['nota_final'], 9.0)
        self.assertEqual(parecer_dados['parecer_final'], parecer_texto)
        self.assertEqual(parecer_dados['supervisor'], self.supervisor.nome)
        self.assertEqual(parecer_dados['aluno'], self.aluno.nome)
    
    def test_get_parecer_para_consulta_nao_disponivel(self):
        """CA6 - Testa que parecer não disponível retorna None"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.0)
        
        parecer_texto = "O estagiário demonstrou bom desempenho durante o período avaliado, cumprindo as expectativas estabelecidas."
        avaliacao.emitir_parecer_final(parecer_texto, disponibilizar_consulta=False)
        
        avaliacao.refresh_from_db()
        parecer_dados = avaliacao.get_parecer_para_consulta()
        
        self.assertIsNone(parecer_dados)
    
    def test_get_parecer_sem_emissao_retorna_none(self):
        """CA6 - Testa que avaliação sem parecer emitido retorna None"""
        from estagio.models import Avaliacao
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        parecer_dados = avaliacao.get_parecer_para_consulta()
        
        self.assertIsNone(parecer_dados)
    
    def test_alternar_disponibilidade_parecer(self):
        """CA6 - Testa alternar disponibilidade do parecer para consulta"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=7.0)
        
        parecer_texto = "O estagiário demonstrou bom desempenho durante o período avaliado, cumprindo as expectativas estabelecidas."
        avaliacao.emitir_parecer_final(parecer_texto, disponibilizar_consulta=True)
        
        avaliacao.refresh_from_db()
        self.assertTrue(avaliacao.parecer_disponivel_consulta)
        
        # Desabilita consulta
        avaliacao.disponibilizar_parecer_consulta(False)
        avaliacao.refresh_from_db()
        self.assertFalse(avaliacao.parecer_disponivel_consulta)
        
        # Habilita novamente
        avaliacao.disponibilizar_parecer_consulta(True)
        avaliacao.refresh_from_db()
        self.assertTrue(avaliacao.parecer_disponivel_consulta)


class EmitirParecerViewTest(TestCase):
    """
    Testes para view de emissão de parecer final pelo supervisor - CA4, CA5
    """
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901238",
            razao_social="Empresa Teste View",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor_view@test.com',
            email='supervisor_view@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno_view@test.com',
            email='aluno_view@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor View',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio Teste View",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno View",
            contato="aluno_view@test.com",
            matricula="VIEW0000001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_emitir_parecer_view_post_sucesso(self):
        """CA4, CA5 - Testa POST para emissão de parecer com sucesso"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        self.client.login(username='supervisor_view@test.com', password='senha123')
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.5)
        
        parecer_texto = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado, com destaque para proatividade."
        
        response = self.client.post(
            reverse('supervisor:emitir_parecer_final', kwargs={'avaliacao_id': avaliacao.id}),
            data={
                'parecer_final': parecer_texto,
                'disponibilizar_consulta': True,
                'confirmar_emissao': True
            }
        )
        
        avaliacao.refresh_from_db()
        
        self.assertEqual(avaliacao.status, 'parecer_emitido')
        self.assertEqual(avaliacao.nota_final, 8.5)
        self.assertEqual(avaliacao.parecer_final, parecer_texto)
        self.assertTrue(avaliacao.parecer_disponivel_consulta)
    
    def test_emitir_parecer_view_parecer_curto_erro(self):
        """CA5 - Testa que view rejeita parecer muito curto"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        self.client.login(username='supervisor_view@test.com', password='senha123')
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.0)
        
        response = self.client.post(
            reverse('supervisor:emitir_parecer_final', kwargs={'avaliacao_id': avaliacao.id}),
            data={
                'parecer_final': 'Curto',
                'disponibilizar_consulta': True,
                'confirmar_emissao': True
            }
        )
        
        avaliacao.refresh_from_db()
        
        # Deve permanecer no status anterior
        self.assertEqual(avaliacao.status, 'enviada')
        self.assertIsNone(avaliacao.parecer_final)


class ConsultaParecerAlunoViewTest(TestCase):
    """
    Testes para view de consulta de parecer pelo aluno - CA6
    """
    
    def setUp(self):
        self.client = Client()
        
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901239",
            razao_social="Empresa Teste Aluno View",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor_aluno_view@test.com',
            email='supervisor_aluno_view@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno_aluno_view@test.com',
            email='aluno_aluno_view@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Aluno View',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio Teste Aluno View",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Aluno View",
            contato="aluno_aluno_view@test.com",
            matricula="ALUV0000001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_listar_pareceres_aluno(self):
        """CA6 - Testa listagem de pareceres disponíveis para aluno"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        self.client.login(username='aluno_aluno_view@test.com', password='senha123')
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=9.0)
        
        parecer_texto = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado."
        avaliacao.emitir_parecer_final(parecer_texto, disponibilizar_consulta=True)
        
        response = self.client.get(reverse('listar_pareceres_aluno'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('avaliacoes', response.context)
        self.assertEqual(len(response.context['avaliacoes']), 1)
    
    def test_consultar_parecer_disponivel(self):
        """CA6 - Testa acesso a parecer disponível"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        self.client.login(username='aluno_aluno_view@test.com', password='senha123')
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.0)
        
        parecer_texto = "O estagiário demonstrou bom desempenho durante o período avaliado, cumprindo as expectativas estabelecidas."
        avaliacao.emitir_parecer_final(parecer_texto, disponibilizar_consulta=True)
        
        response = self.client.get(
            reverse('consultar_parecer', kwargs={'avaliacao_id': avaliacao.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('parecer_dados', response.context)
        self.assertEqual(response.context['parecer_dados']['nota_final'], 8.0)
    
    def test_consultar_parecer_nao_disponivel_redirect(self):
        """CA6 - Testa que parecer não disponível redireciona"""
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        self.client.login(username='aluno_aluno_view@test.com', password='senha123')
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=7.0)
        
        parecer_texto = "O estagiário demonstrou bom desempenho durante o período avaliado, cumprindo as expectativas estabelecidas."
        avaliacao.emitir_parecer_final(parecer_texto, disponibilizar_consulta=False)
        
        response = self.client.get(
            reverse('consultar_parecer', kwargs={'avaliacao_id': avaliacao.id})
        )
        
        # Deve redirecionar pois não está disponível
        self.assertEqual(response.status_code, 302)


class ParecerFinalFormTest(TestCase):
    """
    Testes para o formulário ParecerFinalForm - CA5
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.empresa = Empresa.objects.create(
            cnpj="12345678901240",
            razao_social="Empresa Teste Form",
            rua="Rua Teste",
            numero=100,
            bairro="Centro"
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor_form@test.com',
            email='supervisor_form@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno_form@test.com',
            email='aluno_form@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        self.supervisor = Supervisor.objects.create(
            nome='Supervisor Form',
            contato='11999999999',
            cargo='Gerente',
            empresa=self.empresa,
            usuario=self.usuario_supervisor
        )
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio Teste Form",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=60),
            carga_horaria=20,
            status='em_andamento'
        )
        
        self.aluno = Aluno.objects.create(
            nome="Aluno Form",
            contato="aluno_form@test.com",
            matricula="FORM0000001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao,
            estagio=self.estagio
        )
    
    def test_form_valido_com_parecer_completo(self):
        """CA5 - Testa formulário válido com todos campos preenchidos"""
        from estagio.forms import ParecerFinalForm
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.5)
        
        parecer_texto = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado, com destaque para a proatividade e dedicação."
        
        form = ParecerFinalForm(
            data={
                'parecer_final': parecer_texto,
                'disponibilizar_consulta': True,
                'confirmar_emissao': True
            },
            avaliacao=avaliacao
        )
        
        self.assertTrue(form.is_valid())
    
    def test_form_invalido_parecer_emitido(self):
        """CA5 - Testa que formulário rejeita avaliação com parecer já emitido"""
        from estagio.forms import ParecerFinalForm
        from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
        
        criterio = CriterioAvaliacao.objects.create(nome='Critério', peso=1.0, obrigatorio=True)
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='enviada'
        )
        
        NotaCriterio.objects.create(avaliacao=avaliacao, criterio=criterio, nota=8.0)
        
        parecer_texto = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado."
        avaliacao.emitir_parecer_final(parecer_texto)
        
        # Tenta criar formulário para mesma avaliação
        form = ParecerFinalForm(
            data={
                'parecer_final': 'Novo parecer com mais de cinquenta caracteres para validar a regra.',
                'disponibilizar_consulta': True,
                'confirmar_emissao': True
            },
            avaliacao=avaliacao
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('já foi emitido', str(form.errors))
    
    def test_form_invalido_avaliacao_rascunho(self):
        """CA5 - Testa que formulário rejeita avaliação em rascunho"""
        from estagio.forms import ParecerFinalForm
        from estagio.models import Avaliacao
        
        avaliacao = Avaliacao.objects.create(
            supervisor=self.supervisor,
            estagio=self.estagio,
            aluno=self.aluno,
            data_avaliacao=date.today(),
            periodo='mensal',
            periodo_inicio=date.today() - timedelta(days=30),
            periodo_fim=date.today(),
            status='rascunho'
        )
        
        parecer_texto = "O estagiário demonstrou excelente desempenho em todas as atividades propostas durante o período avaliado."
        
        form = ParecerFinalForm(
            data={
                'parecer_final': parecer_texto,
                'disponibilizar_consulta': True,
                'confirmar_emissao': True
            },
            avaliacao=avaliacao
        )
        
        self.assertFalse(form.is_valid())