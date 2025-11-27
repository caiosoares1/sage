"""
Testes adicionais para aumentar cobertura de estagio/views.py
"""
from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
from users.models import Usuario
from admin.models import Instituicao, CursoCoordenador, Empresa, Supervisor
from estagio.models import Aluno, Estagio, Documento


class ListarDocumentosViewTest(TestCase):
    """Testes para view listar_documentos"""
    
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
    
    def test_aluno_pode_listar_documentos(self):
        """Testa que aluno pode acessar lista de documentos"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('listar_documentos'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('documentos', response.context)


class HistoricoDocumentoViewTest(TestCase):
    """Testes para view historico_documento"""
    
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
            nome_arquivo="teste.pdf",
            tipo="Plano de Estágio",
            arquivo="docs/teste.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="enviado"
        )
    
    def test_aluno_pode_ver_historico(self):
        """Testa que aluno pode ver histórico do documento"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('historico_documento', args=[self.documento.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('historico', response.context)


class AcompanharEstagiosAdicionaisViewTest(TestCase):
    """Testes adicionais para view acompanhar_estagios"""
    
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
    
    def test_aluno_sem_estagio_ve_mensagem(self):
        """Testa que aluno sem estágio vê mensagem apropriada"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('acompanhar_estagios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagios', response.context)
    
    def test_aluno_com_estagio_ve_detalhes(self):
        """Testa que aluno com estágio vê os detalhes"""
        # Criar estágio
        estagio = Estagio.objects.create(
            titulo="Estágio de Teste",
            cargo="Desenvolvedor",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status="aprovado"
        )
        
        self.aluno.estagio = estagio
        self.aluno.save()
        
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('acompanhar_estagios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagios', response.context)


class EstagioDetalheAdicionaisViewTest(TestCase):
    """Testes adicionais para view estagio_detalhe"""
    
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
    
    def test_aluno_pode_ver_detalhes_completos(self):
        """Testa que aluno pode ver todos os detalhes do estágio"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('estagio_detalhe', args=[self.estagio.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagio', response.context)
        self.assertEqual(response.context['estagio'].titulo, 'Estágio de Teste')
    
    def test_detalhes_estagio_com_documentos(self):
        """Testa detalhes do estágio quando há documentos"""
        # Criar documento
        Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="teste.pdf",
            tipo="Plano de Estágio",
            arquivo="docs/teste.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="enviado"
        )
        
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('estagio_detalhe', args=[self.estagio.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('documentos', response.context)


class SolicitarEstagioValidacoesTest(TestCase):
    """Testes adicionais para validações em solicitar_estagio"""
    
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
    
    def test_solicitar_estagio_com_dados_invalidos(self):
        """Testa que formulário inválido retorna erro"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        # Enviar dados incompletos
        response = self.client.post(reverse('solicitar_estagio'), {
            'titulo': '',  # Campo obrigatório vazio
            'cargo': 'Desenvolvedor'
        })
        
        # Deve retornar o formulário com erros
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagio_form', response.context)


class ListarDocumentosAdicionaisTest(TestCase):
    """Testes adicionais para listar documentos com cenários variados"""
    
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
    
    def test_listar_documentos_com_multiplos_documentos(self):
        """Testa listagem quando há múltiplos documentos"""
        # Criar múltiplos documentos
        for i in range(3):
            Documento.objects.create(
                data_envio=date.today(),
                versao=float(i + 1),
                nome_arquivo=f"documento{i}.pdf",
                tipo="Plano de Estágio",
                arquivo=f"docs/doc{i}.pdf",
                estagio=self.estagio,
                supervisor=self.supervisor,
                coordenador=self.coordenador,
                enviado_por=self.usuario_aluno,
                status="enviado"
            )
        
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('listar_documentos'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('documentos', response.context)
        self.assertEqual(len(response.context['documentos']), 3)
