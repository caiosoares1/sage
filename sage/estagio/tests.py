"""
Testes para as views de aluno do sistema de estágios
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from estagio.models import Aluno, Estagio, Documento, DocumentoHistorico, HorasCumpridas, Notificacao
from admin.models import Instituicao, Empresa, Supervisor, CursoCoordenador
from users.models import Usuario
from django.db.models import Sum
from django.utils import timezone


class SupervisorVerHorasViewTest(TestCase):
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
        self.supervisor = Supervisor.objects.create(
            usuario=self.usuario_supervisor,
            nome="Supervisor Teste",
            contato="11988888888",
            cargo="Gerente",
            empresa=self.empresa
        )
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno1@test.com',
            email='aluno1@test.com',
            password='senha123',
            tipo='aluno'
        )
        self.aluno = Aluno.objects.create(
            usuario=self.usuario_aluno,
            nome='Aluno Horas',
            contato='horas@email.com',
            matricula='20238888',
            instituicao=self.instituicao
        )
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
        self.url = reverse('supervisor_ver_horas')

    def test_permissao_apenas_supervisor(self):
        # CA5 - Permissão
        usuario_aluno = Usuario.objects.create_user(
            username='aluno2@test.com',
            email='aluno2@test.com',
            password='senha123',
            tipo='aluno'
        )
        self.client.login(username='aluno2@test.com', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        # Redireciona para dashboard

    def test_visualizacao_horas_supervisor(self):
        # CA1, CA2, CA3, CA4, CA8
        self.client.login(username='supervisor@test.com', password='senha123')
        # Adiciona registros de horas
        HorasCumpridas.objects.create(aluno=self.aluno, data=date(2025,12,1), quantidade=5, descricao='Lab')
        HorasCumpridas.objects.create(aluno=self.aluno, data=date(2025,12,2), quantidade=3, descricao='Seminário')
        HorasCumpridas.objects.create(aluno=self.aluno, data=date(2025,11,30), quantidade=2, descricao='Reunião')
        # Pesquisa pelo aluno
        response = self.client.get(self.url, {'aluno': self.aluno.id})
        self.assertEqual(response.status_code, 200)
        # CA2 - Total de horas
        self.assertIn('total_horas', response.context)
        self.assertEqual(response.context['total_horas'], 10)
        # CA3 - Lista detalhada
        horas_list = response.context['horas_list']
        self.assertEqual(len(horas_list), 3)
        self.assertEqual(horas_list[0].data, date(2025,12,2))  # Mais recente primeiro
        self.assertEqual(horas_list[1].data, date(2025,12,1))
        self.assertEqual(horas_list[2].data, date(2025,11,30))
        # CA4 - Seleção do aluno
        self.assertEqual(response.context['aluno_selecionado'], self.aluno)
        # CA7 - Atualização automática
        HorasCumpridas.objects.create(aluno=self.aluno, data=date(2025,12,3), quantidade=1, descricao='Extra')
        response2 = self.client.get(self.url, {'aluno': self.aluno.id})
        self.assertEqual(response2.context['total_horas'], 11)
        self.assertEqual(response2.context['horas_list'][0].data, date(2025,12,3))


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


class CadastroAlunoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        self.usuario = Usuario.objects.create_user(
            username='novoaluno@test.com',
            email='novoaluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        self.url = reverse('cadastrar_aluno')

    def test_cadastro_sucesso(self):
        self.client.login(username='novoaluno@test.com', password='senha123')
        data = {
            'nome': 'Aluno Teste',
            'contato': 'aluno@email.com',
            'matricula': '20231234',
            'instituicao': self.instituicao.id
        }
        response = self.client.post(self.url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Aluno.objects.filter(matricula='20231234').exists())
        messages_list = list(get_messages(response.wsgi_request))
        self.assertIn('Cadastro realizado com sucesso!', [m.message for m in messages_list])

    def test_cadastro_duplicidade_matricula(self):
        Aluno.objects.create(
            usuario=self.usuario,
            nome='Aluno Teste',
            contato='aluno@email.com',
            matricula='20231234',
            instituicao=self.instituicao
        )
        self.client.login(username='novoaluno@test.com', password='senha123')
        data = {
            'nome': 'Outro Aluno',
            'contato': 'outro@email.com',
            'matricula': '20231234',
            'instituicao': self.instituicao.id
        }
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'matricula', 'Esta matrícula já está cadastrada.')

    def test_nome_apenas_letras(self):
        self.client.login(username='novoaluno@test.com', password='senha123')
        data = {
            'nome': 'Aluno123',
            'contato': 'aluno@email.com',
            'matricula': '20231235',
            'instituicao': self.instituicao.id
        }
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'nome', 'O nome deve conter apenas letras.')

    def test_contato_email_obrigatorio(self):
        self.client.login(username='novoaluno@test.com', password='senha123')
        data = {
            'nome': 'Aluno Teste',
            'contato': '',
            'matricula': '20231236',
            'instituicao': self.instituicao.id
        }
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'contato', 'O campo E-mail é obrigatório.')

    def test_matricula_apenas_numeros(self):
        self.client.login(username='novoaluno@test.com', password='senha123')
        data = {
            'nome': 'Aluno Teste',
            'contato': 'aluno@email.com',
            'matricula': 'ABC123',
            'instituicao': self.instituicao.id
        }
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'matricula', 'A matrícula deve conter apenas números.')

    def test_campos_obrigatorios(self):
        self.client.login(username='novoaluno@test.com', password='senha123')
        data = {
            'nome': '',
            'contato': '',
            'matricula': '',
            'instituicao': self.instituicao.id
        }
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'nome', 'O campo Nome é obrigatório.')
        self.assertFormError(response, 'form', 'contato', 'O campo E-mail é obrigatório.')
        self.assertFormError(response, 'form', 'matricula', 'O campo Matrícula é obrigatório.')


class CadastroHorasViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        self.usuario = Usuario.objects.create_user(
            username='alunohoras@test.com',
            email='alunohoras@test.com',
            password='senha123',
            tipo='aluno'
        )
        self.aluno = Aluno.objects.create(
            usuario=self.usuario,
            nome='Aluno Horas',
            contato='horas@email.com',
            matricula='20238888',
            instituicao=self.instituicao
        )
        self.url = reverse('cadastrar_horas')

    def test_cadastro_sucesso_e_soma(self):
        self.client.login(username='alunohoras@test.com', password='senha123')
        data = {
            'data': '2025-12-01',
            'quantidade': 5,
            'descricao': 'Atividades de laboratório'
        }
        response = self.client.post(self.url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.aluno.horas.filter(quantidade=5).exists())
        messages_list = list(get_messages(response.wsgi_request))
        # Corrige assert para mensagem de sucesso
        self.assertTrue(any('Horas cadastradas com sucesso!' in m.message for m in messages_list))
        # Soma automática
        data2 = {
            'data': '2025-12-02',
            'quantidade': 3,
            'descricao': 'Seminário'
        }
        self.client.post(self.url, data2)
        total = self.aluno.horas.aggregate(total=Sum('quantidade'))['total']
        self.assertEqual(total, 8)

    def test_obrigatoriedade_campos(self):
        self.client.login(username='alunohoras@test.com', password='senha123')
        data = {'data': '', 'quantidade': '', 'descricao': ''}
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'data', 'O campo data é obrigatório.')
        self.assertFormError(response, 'form', 'quantidade', 'O campo quantidade de horas é obrigatório.')
        self.assertFormError(response, 'form', 'descricao', 'O campo descrição é obrigatório.')

    def test_data_futura(self):
        from datetime import date, timedelta
        self.client.login(username='alunohoras@test.com', password='senha123')
        futura = (date.today() + timedelta(days=1)).isoformat()
        data = {'data': futura, 'quantidade': 2, 'descricao': 'Teste'}
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'data', 'Não é permitido cadastrar horas em data futura.')

    def test_quantidade_invalida(self):
        self.client.login(username='alunohoras@test.com', password='senha123')
        # Não numérico
        data = {'data': '2025-12-01', 'quantidade': 'abc', 'descricao': 'Teste'}
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'quantidade', 'A quantidade de horas deve ser numérica e maior que zero.')
        # Menor ou igual a zero
        data = {'data': '2025-12-01', 'quantidade': 0, 'descricao': 'Teste'}
        response = self.client.post(self.url, data)
        self.assertFormError(response, 'form', 'quantidade', 'A quantidade de horas deve ser numérica e maior que zero.')


class NotificacaoPrazosProximosTest(TestCase):
    """Testes para notificações de prazos próximos - US Recebimento de notificações sobre prazos próximos"""
    
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
        self.supervisor = Supervisor.objects.create(
            usuario=self.usuario_supervisor,
            nome="Supervisor Teste",
            contato="11988888888",
            cargo="Gerente",
            empresa=self.empresa
        )
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
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
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        self.aluno = Aluno.objects.create(
            usuario=self.usuario_aluno,
            nome='Aluno Teste',
            contato='aluno@email.com',
            matricula='20230001',
            instituicao=self.instituicao
        )
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

    @patch('estagio.views.enviar_notificacao_email')
    def test_ca1_identifica_documentos_prazos_proximos(self, mock_email):
        """CA1 - O sistema deve identificar documentos com prazos próximos automaticamente"""
        from estagio.views import verificar_prazos_proximos
        
        # Documento com prazo em 2 dias (dentro do período de alerta)
        doc_prazo_proximo = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_prazo_proximo.pdf",
            tipo="termo_compromisso",
            status='ajustes_solicitados',
            prazo_limite=date.today() + timedelta(days=2),
            enviado_por=self.usuario_aluno
        )
        
        # Documento com prazo em 10 dias (fora do período de alerta)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_prazo_longe.pdf",
            tipo="relatorio",
            status='ajustes_solicitados',
            prazo_limite=date.today() + timedelta(days=10),
            enviado_por=self.usuario_aluno
        )
        
        notificacoes = verificar_prazos_proximos(dias_alerta=3)
        
        # Deve identificar apenas o documento com prazo próximo
        self.assertEqual(len(notificacoes), 1)
        self.assertIn('doc_prazo_proximo.pdf', notificacoes[0].assunto)

    @patch('estagio.views.enviar_notificacao_email')
    def test_ca2_envia_notificacao_periodo_minimo(self, mock_email):
        """CA2 - O sistema deve enviar notificação ao aluno quando faltar o período mínimo definido"""
        from estagio.views import verificar_prazos_proximos
        
        # Documento com prazo em 3 dias
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_teste.pdf",
            tipo="termo_compromisso",
            status='ajustes_solicitados',
            prazo_limite=date.today() + timedelta(days=3),
            enviado_por=self.usuario_aluno
        )
        
        notificacoes = verificar_prazos_proximos(dias_alerta=3)
        
        self.assertEqual(len(notificacoes), 1)
        # Verifica que a notificação foi criada para o email do aluno
        self.assertEqual(notificacoes[0].destinatario, self.aluno.contato)

    @patch('estagio.views.enviar_notificacao_email')
    def test_ca3_notificacao_informa_documento_e_data(self, mock_email):
        """CA3 - A notificação deve informar o nome do documento e a data limite"""
        from estagio.views import verificar_prazos_proximos
        
        prazo = date.today() + timedelta(days=2)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="relatorio_mensal.pdf",
            tipo="relatorio",
            status='reprovado',
            prazo_limite=prazo,
            enviado_por=self.usuario_aluno
        )
        
        notificacoes = verificar_prazos_proximos(dias_alerta=3)
        
        self.assertEqual(len(notificacoes), 1)
        # Verifica que a notificação contém o nome do documento
        self.assertIn('relatorio_mensal.pdf', notificacoes[0].assunto)
        # Verifica que a notificação contém a data limite
        self.assertIn(prazo.strftime('%d/%m/%Y'), notificacoes[0].mensagem)

    @patch('estagio.views.enviar_notificacao_email')
    def test_ca4_nao_envia_para_documentos_entregues(self, mock_email):
        """CA4 - O sistema não deve enviar notificações para documentos já entregues"""
        from estagio.views import verificar_prazos_proximos
        
        # Documento aprovado (já entregue)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_aprovado.pdf",
            tipo="termo_compromisso",
            status='aprovado',
            prazo_limite=date.today() + timedelta(days=2),
            enviado_por=self.usuario_aluno
        )
        
        # Documento finalizado (já entregue)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_finalizado.pdf",
            tipo="relatorio",
            status='finalizado',
            prazo_limite=date.today() + timedelta(days=2),
            enviado_por=self.usuario_aluno
        )
        
        # Documento enviado (em análise)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_enviado.pdf",
            tipo="avaliacao",
            status='enviado',
            prazo_limite=date.today() + timedelta(days=2),
            enviado_por=self.usuario_aluno
        )
        
        notificacoes = verificar_prazos_proximos(dias_alerta=3)
        
        # Não deve enviar notificações para documentos já entregues
        self.assertEqual(len(notificacoes), 0)

    @patch('estagio.views.enviar_notificacao_email')
    def test_ca5_impede_notificacoes_duplicadas(self, mock_email):
        """CA5 - O sistema deve impedir o envio de notificações duplicadas para o mesmo prazo"""
        from estagio.views import verificar_prazos_proximos
        
        prazo = date.today() + timedelta(days=2)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_teste.pdf",
            tipo="termo_compromisso",
            status='ajustes_solicitados',
            prazo_limite=prazo,
            enviado_por=self.usuario_aluno
        )
        
        # Primeira execução - deve criar notificação
        notificacoes1 = verificar_prazos_proximos(dias_alerta=3)
        self.assertEqual(len(notificacoes1), 1)
        
        # Segunda execução - não deve criar notificação duplicada
        notificacoes2 = verificar_prazos_proximos(dias_alerta=3)
        self.assertEqual(len(notificacoes2), 0)
        
        # Verifica que existe apenas uma notificação no banco
        total_notificacoes = Notificacao.objects.filter(destinatario=self.aluno.contato).count()
        self.assertEqual(total_notificacoes, 1)

    @patch('estagio.views.enviar_notificacao_email')
    def test_ca6_registra_data_hora_envio(self, mock_email):
        """CA6 - O sistema deve registrar a data e hora em que a notificação foi enviada"""
        from estagio.views import verificar_prazos_proximos
        
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_teste.pdf",
            tipo="termo_compromisso",
            status='ajustes_solicitados',
            prazo_limite=date.today() + timedelta(days=2),
            enviado_por=self.usuario_aluno
        )
        
        antes = timezone.now()
        notificacoes = verificar_prazos_proximos(dias_alerta=3)
        depois = timezone.now()
        
        self.assertEqual(len(notificacoes), 1)
        # Verifica que a data de envio foi registrada
        self.assertIsNotNone(notificacoes[0].data_envio)
        # Verifica que a data está dentro do intervalo esperado
        self.assertTrue(antes <= notificacoes[0].data_envio <= depois)

    def test_ca7_aluno_visualiza_notificacoes_recentes(self):
        """CA7 - O sistema deve permitir que o aluno visualize as notificações recentes na área de avisos"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        # Cria notificações para o aluno
        Notificacao.objects.create(
            destinatario=self.aluno.contato,
            assunto="Alerta: Prazo próximo para o documento doc1.pdf",
            mensagem="O prazo termina em 2 dias",
            referencia="alerta_prazo_1_2025-12-13"
        )
        Notificacao.objects.create(
            destinatario=self.aluno.contato,
            assunto="Alerta: Prazo próximo para o documento doc2.pdf",
            mensagem="O prazo termina em 1 dia",
            referencia="alerta_prazo_2_2025-12-12"
        )
        
        # Acessa a API de notificações
        response = self.client.get(reverse('api_notificacoes'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['notificacoes']), 2)

    def test_bdd_cenario_completo(self):
        """
        BDD: DADO que o aluno possui documentos com prazos próximos
        QUANDO faltar o período mínimo definido para o vencimento
        ENTÃO o sistema deve enviar notificação informando o prazo e o documento
        """
        from estagio.views import verificar_prazos_proximos
        
        # DADO que o aluno possui documentos com prazos próximos
        prazo = date.today() + timedelta(days=2)  # 2 dias - dentro do período de 3 dias
        doc = Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo_compromisso_v1.pdf",
            tipo="termo_compromisso",
            status='ajustes_solicitados',
            prazo_limite=prazo,
            enviado_por=self.usuario_aluno
        )
        
        # QUANDO faltar o período mínimo definido para o vencimento
        with patch('estagio.views.enviar_notificacao_email') as mock_email:
            notificacoes = verificar_prazos_proximos(dias_alerta=3)
        
        # ENTÃO o sistema deve enviar notificação informando o prazo e o documento
        self.assertEqual(len(notificacoes), 1)
        notificacao = notificacoes[0]
        
        # Verifica que informa o documento
        self.assertIn(doc.nome_arquivo, notificacao.assunto)
        
        # Verifica que informa o prazo
        self.assertIn(prazo.strftime('%d/%m/%Y'), notificacao.mensagem)
        
        # Verifica que foi enviada para o aluno
        self.assertEqual(notificacao.destinatario, self.aluno.contato)

