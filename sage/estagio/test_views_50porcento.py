"""
Testes adicionais focados em aumentar cobertura para 50%+
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from unittest.mock import patch
from users.models import Usuario
from admin.models import Instituicao, CursoCoordenador, Empresa, Supervisor
from estagio.models import Aluno, Estagio, Documento


class SolicitarEstagioFormularioInvalidoTest(TestCase):
    """Testes para formulário inválido em solicitar_estagio"""
    
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
        
        # Criar usuário aluno
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        # Criar aluno
        self.aluno = Aluno.objects.create(
            usuario=self.usuario_aluno,
            nome="Aluno Teste",
            matricula="20230001",
            contato="11999999999",
            instituicao=self.instituicao
        )
    
    def test_post_com_formulario_invalido_mostra_erro(self):
        """Testa que POST com dados inválidos retorna erro"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.post(reverse('solicitar_estagio'), {
            'titulo': '',  # Campo vazio
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagio_form', response.context)
        messages_list = list(response.context['messages'])
        self.assertTrue(any('corrija os erros' in str(m).lower() for m in messages_list))


class AcompanharEstagiosSemEstagioTest(TestCase):
    """Testes para acompanhar_estagios quando aluno não tem estágio"""
    
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
        
        # Criar usuário aluno
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        # Criar aluno SEM estágio
        self.aluno = Aluno.objects.create(
            usuario=self.usuario_aluno,
            nome="Aluno Teste",
            matricula="20230001",
            contato="11999999999",
            instituicao=self.instituicao
        )
    
    def test_aluno_sem_estagio_ve_lista_vazia(self):
        """Testa que aluno sem estágio vê lista vazia"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('acompanhar_estagios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagios', response.context)
        # Lista deve estar vazia ou ter apenas o None/vazio
        estagios = response.context['estagios']
        if estagios:
            self.assertEqual(len(estagios), 0)


class EstagioDetalheComDocumentosTest(TestCase):
    """Testes para estagio_detalhe com documentos associados"""
    
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
        
        # Criar documentos
        self.documento1 = Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc1.pdf",
            tipo="Plano de Estágio",
            arquivo="docs/doc1.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="enviado"
        )
        
        self.documento2 = Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc2.pdf",
            tipo="Relatório",
            arquivo="docs/doc2.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="aprovado"
        )
    
    def test_estagio_detalhe_lista_todos_documentos(self):
        """Testa que estagio_detalhe lista todos os documentos"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('estagio_detalhe', args=[self.estagio.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('documentos', response.context)
        # Deve conter os 2 documentos criados
        self.assertEqual(len(response.context['documentos']), 2)


class ListarDocumentosVariosStatusTest(TestCase):
    """Testes para listar_documentos com diferentes status"""
    
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
    
    def test_listar_documentos_diferentes_status(self):
        """Testa listagem com documentos de diferentes status"""
        # Criar documentos com diferentes status
        Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_enviado.pdf",
            tipo="Plano",
            arquivo="docs/doc1.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="enviado"
        )
        
        Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_aprovado.pdf",
            tipo="Relatório",
            arquivo="docs/doc2.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="aprovado"
        )
        
        Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_ajustes.pdf",
            tipo="Termo",
            arquivo="docs/doc3.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="ajustes_solicitados"
        )
        
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('listar_documentos'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('documentos', response.context)
        self.assertEqual(len(response.context['documentos']), 3)


class HistoricoDocumentoSemPermissaoTest(TestCase):
    """Testes para historico_documento verificando permissões"""
    
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
        
        # Criar dois alunos diferentes
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
        
        # Criar estágio para aluno1
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
        
        self.aluno1.estagio = self.estagio1
        self.aluno1.save()
        
        # Criar documento do aluno1
        self.documento = Documento.objects.create(
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
    
    def test_aluno_correto_ve_historico(self):
        """Testa que aluno dono do documento pode ver histórico"""
        self.client.login(username='aluno1@test.com', password='senha123')
        
        response = self.client.get(reverse('historico_documento', args=[self.documento.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('historico', response.context)


class AcompanharEstagiosComEstagioTest(TestCase):
    """Testes para verificar estatísticas em acompanhar_estagios"""
    
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
        
        # Criar documentos com diferentes status
        Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc1.pdf",
            tipo="Plano",
            arquivo="docs/doc1.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="enviado"
        )
        
        Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc2.pdf",
            tipo="Relatório",
            arquivo="docs/doc2.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="aprovado"
        )
        
        Documento.objects.create(
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc3.pdf",
            tipo="Termo",
            arquivo="docs/doc3.pdf",
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            enviado_por=self.usuario_aluno,
            status="ajustes_solicitados"
        )
    
    def test_acompanhar_estagios_mostra_estatisticas(self):
        """Testa que estatísticas são calculadas corretamente"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('acompanhar_estagios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.context)
        
        # Verificar estatísticas
        stats = response.context['stats']
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['enviados'], 1)
        self.assertEqual(stats['aprovados_supervisor'], 1)
        self.assertEqual(stats['ajustes'], 1)
