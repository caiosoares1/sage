"""
Testes para os models do sistema
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from estagio.models import Aluno, Estagio, Documento, DocumentoHistorico, Avaliacao
from admin.models import Instituicao, Empresa, Supervisor, CursoCoordenador
from users.models import Usuario


class AlunoModelTest(TestCase):
    """Testes para o modelo Aluno"""
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        self.usuario = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
    
    def test_criar_aluno(self):
        """Testa criação de um aluno"""
        aluno = Aluno.objects.create(
            usuario=self.usuario,
            nome="João Silva",
            matricula="20230001",
            contato="11999999999",
            instituicao=self.instituicao
        )
        
        self.assertEqual(aluno.nome, "João Silva")
        self.assertEqual(aluno.matricula, "20230001")
        self.assertEqual(str(aluno), "João Silva - 20230001")
    
    def test_aluno_matricula_unica(self):
        """Testa se matrícula é única"""
        Aluno.objects.create(
            usuario=self.usuario,
            nome="João Silva",
            matricula="20230001",
            contato="11999999999",
            instituicao=self.instituicao
        )
        
        # Criar outro usuário para o segundo aluno
        usuario2 = Usuario.objects.create_user(
            username='aluno2@test.com',
            email='aluno2@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        # Tentar criar outro aluno com mesma matrícula deve falhar
        with self.assertRaises(Exception):
            Aluno.objects.create(
                usuario=usuario2,
                nome="Maria Santos",
                matricula="20230001",
                contato="11988888888",
                instituicao=self.instituicao
            )
    
    def test_aluno_relacionamento_com_usuario(self):
        """Testa relacionamento OneToOne com Usuario"""
        aluno = Aluno.objects.create(
            usuario=self.usuario,
            nome="João Silva",
            matricula="20230001",
            contato="11999999999",
            instituicao=self.instituicao
        )
        
        self.assertEqual(self.usuario.aluno, aluno)
        self.assertEqual(aluno.usuario.username, 'aluno@test.com')


class EstagioModelTest(TestCase):
    """Testes para o modelo Estagio"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste",
            cnpj="98765432109876",
            numero=456,
            bairro="Centro",
            rua="Av Teste"
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
    
    def test_criar_estagio(self):
        """Testa criação de um estágio"""
        estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20,
            status='analise'
        )
        
        self.assertEqual(estagio.titulo, "Estágio em TI")
        self.assertEqual(estagio.status, 'analise')
        self.assertEqual(str(estagio), "Estágio em TI")
    
    def test_estagio_status_choices(self):
        """Testa as opções de status do estágio"""
        estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
        
        # Testar mudança de status
        estagio.status = 'aprovado'
        estagio.save()
        self.assertEqual(estagio.status, 'aprovado')
        
        estagio.status = 'reprovado'
        estagio.save()
        self.assertEqual(estagio.status, 'reprovado')


class DocumentoModelTest(TestCase):
    """Testes para o modelo Documento"""
    
    def setUp(self):
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
        
        usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        # Criar entidades
        self.aluno = Aluno.objects.create(
            usuario=usuario_aluno,
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
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
    
    def test_criar_documento(self):
        """Testa criação de um documento"""
        documento = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo_compromisso.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario
        )
        
        self.assertEqual(documento.versao, 1.0)
        self.assertEqual(documento.status, 'enviado')
        self.assertEqual(str(documento), "termo_compromisso.pdf")
    
    def test_documento_status_choices(self):
        """Testa as opções de status do documento"""
        documento = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo_compromisso.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario
        )
        
        # Testar mudanças de status
        statuses = ['enviado', 'ajustes_solicitados', 'corrigido', 'aprovado', 'reprovado', 'substituido', 'finalizado']
        for status in statuses:
            documento.status = status
            documento.save()
            self.assertEqual(documento.status, status)
    
    def test_documento_get_history_sem_parent(self):
        """Testa get_history() para documento sem versões anteriores"""
        documento = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo_compromisso.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario
        )
        
        history = documento.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0], documento)
    
    def test_documento_get_history_com_versoes(self):
        """Testa get_history() para documento com múltiplas versões"""
        # Criar versão 1.0
        doc_v1 = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo_v1.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario
        )
        
        # Criar versão 2.0 (filho de 1.0)
        doc_v2 = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today() + timedelta(days=1),
            versao=2.0,
            nome_arquivo="termo_v2.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario,
            parent=doc_v1
        )
        
        # Criar versão 3.0 (filho de 2.0)
        doc_v3 = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today() + timedelta(days=2),
            versao=3.0,
            nome_arquivo="termo_v3.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario,
            parent=doc_v2
        )
        
        # Verificar histórico da versão 3.0
        history = doc_v3.get_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0], doc_v1)  # Mais antigo
        self.assertEqual(history[1], doc_v2)
        self.assertEqual(history[2], doc_v3)  # Mais recente
    
    def test_documento_parent_relationship(self):
        """Testa relacionamento parent-child entre documentos"""
        doc_parent = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo_v1.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario
        )
        
        doc_child = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today() + timedelta(days=1),
            versao=2.0,
            nome_arquivo="termo_v2.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario,
            parent=doc_parent
        )
        
        self.assertEqual(doc_child.parent, doc_parent)
        self.assertIn(doc_child, doc_parent.versions.all())


class DocumentoHistoricoModelTest(TestCase):
    """Testes para o modelo DocumentoHistorico"""
    
    def setUp(self):
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
        
        usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        
        # Criar entidades
        self.aluno = Aluno.objects.create(
            usuario=usuario_aluno,
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
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
        
        # Criar documento
        self.documento = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo_compromisso.pdf",
            tipo="termo_compromisso",
            enviado_por=self.aluno.usuario
        )
    
    def test_criar_historico(self):
        """Testa criação de registro de histórico"""
        historico = DocumentoHistorico.objects.create(
            documento=self.documento,
            acao='enviado',
            usuario=self.aluno.usuario,
            observacoes="Documento inicial enviado"
        )
        
        self.assertEqual(historico.acao, 'enviado')
        self.assertEqual(historico.usuario, self.aluno.usuario)
        self.assertIsNotNone(historico.data_hora)
    
    def test_historico_acao_choices(self):
        """Testa as opções de ação do histórico"""
        acoes = ['enviado', 'aprovado', 'reprovado', 'ajustes_solicitados', 'corrigido', 'finalizado']
        
        for acao in acoes:
            historico = DocumentoHistorico.objects.create(
                documento=self.documento,
                acao=acao,
                usuario=self.aluno.usuario
            )
            self.assertEqual(historico.acao, acao)
    
    def test_historico_ordering(self):
        """Testa se históricos são ordenados por data_hora descendente"""
        # Criar vários históricos
        h1 = DocumentoHistorico.objects.create(
            documento=self.documento,
            acao='enviado',
            usuario=self.aluno.usuario
        )
        
        h2 = DocumentoHistorico.objects.create(
            documento=self.documento,
            acao='aprovado',
            usuario=self.supervisor.usuario
        )
        
        h3 = DocumentoHistorico.objects.create(
            documento=self.documento,
            acao='finalizado',
            usuario=self.coordenador.usuario
        )
        
        # Buscar históricos
        historicos = DocumentoHistorico.objects.filter(documento=self.documento)
        
        # Verificar ordem (mais recente primeiro)
        self.assertEqual(historicos[0], h3)
        self.assertEqual(historicos[1], h2)
        self.assertEqual(historicos[2], h1)


class AvaliacaoModelTest(TestCase):
    """Testes para o modelo Avaliacao"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste",
            cnpj="98765432109876",
            numero=456,
            bairro="Centro",
            rua="Av Teste"
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
        
        self.estagio = Estagio.objects.create(
            titulo="Estágio em TI",
            cargo="Desenvolvedor Junior",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=20
        )
    
    def test_criar_avaliacao(self):
        """Testa criação de uma avaliação"""
        avaliacao = Avaliacao.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            parecer="Excelente desempenho",
            nota=9.5,
            data_avaliacao=date.today()
        )
        
        self.assertEqual(avaliacao.nota, 9.5)
        self.assertEqual(avaliacao.parecer, "Excelente desempenho")
        self.assertIn("Avaliação", str(avaliacao))
