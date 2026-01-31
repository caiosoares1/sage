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


# ==================== TESTES DO PAINEL DE STATUS DE ESTÁGIOS ====================

class PainelEstagiosViewBaseTest(TestCase):
    """
    Classe base com setup comum para testes do painel de estágios.
    """
    
    def setUp(self):
        self.client = Client()
        
        # Cria instituição
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        # Cria empresa
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste",
            cnpj="98765432109876",
            numero=456,
            bairro="Centro",
            rua="Av Teste"
        )
        
        # Cria usuário coordenador
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        self.coordenador = CursoCoordenador.objects.create(
            usuario=self.usuario_coordenador,
            nome="Coordenador Teste",
            contato="11977777777",
            instituicao=self.instituicao
        )
        
        # Cria usuário supervisor
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
        
        # Cria usuário aluno
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="11999999999",
            matricula="20240001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao
        )
        
        # Cria estágios com diferentes status
        self.estagio_analise = Estagio.objects.create(
            titulo="Estágio Análise",
            cargo="Estagiário",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='analise',
            aluno_solicitante=self.aluno
        )
        
        self.estagio_em_andamento = Estagio.objects.create(
            titulo="Estágio Em Andamento",
            cargo="Desenvolvedor Jr",
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=150),
            carga_horaria=30,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='em_andamento',
            aluno_solicitante=self.aluno
        )
        
        self.estagio_aprovado = Estagio.objects.create(
            titulo="Estágio Aprovado",
            cargo="Analista",
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=120),
            carga_horaria=40,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='aprovado',
            aluno_solicitante=self.aluno
        )


class PainelEstagiosViewCA1Test(PainelEstagiosViewBaseTest):
    """
    Testes para CA1 - O sistema deve permitir a exibição de estágios por status.
    
    US: Visualização em painel dos status dos estágios
    
    BDD:
    DADO que existem estágios cadastrados
    QUANDO o usuário acessar o painel
    ENTÃO deve visualizar o status atualizado dos estágios
    """
    
    def test_ca1_exibir_estagios_por_status(self):
        """CA1 - Testa exibição de estágios agrupados por status"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagios_por_status', response.context)
        
        estagios_por_status = response.context['estagios_por_status']
        self.assertEqual(estagios_por_status['analise'].count(), 1)
        self.assertEqual(estagios_por_status['em_andamento'].count(), 1)
        self.assertEqual(estagios_por_status['aprovado'].count(), 1)
    
    def test_ca1_filtro_por_status(self):
        """CA1 - Testa filtro de estágios por status específico"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('painel_estagios'), {'status': 'analise'})
        
        self.assertEqual(response.status_code, 200)
        estagios = response.context['estagios']
        
        # Verifica que todos os estágios retornados têm o status filtrado
        for estagio in estagios:
            self.assertEqual(estagio.status, 'analise')
    
    def test_ca1_estatisticas_por_status(self):
        """CA1 - Testa cálculo de estatísticas por status"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        estatisticas = response.context['estatisticas']
        
        self.assertEqual(estatisticas['total'], 3)
        self.assertEqual(estatisticas['analise'], 1)
        self.assertEqual(estatisticas['em_andamento'], 1)
        self.assertEqual(estatisticas['aprovado'], 1)
    
    def test_ca1_api_estagios_por_status(self):
        """CA1 - Testa API para obter estágios por status específico"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_estagios_por_status', args=['em_andamento']))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'em_andamento')
        self.assertEqual(data['total'], 1)
    
    def test_ca1_api_status_invalido_retorna_erro(self):
        """CA1 - Testa que API retorna erro para status inválido"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_estagios_por_status', args=['invalido']))
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_ca1_bdd_visualizar_status_atualizado(self):
        """
        BDD: DADO que existem estágios cadastrados
             QUANDO o usuário acessar o painel
             ENTÃO deve visualizar o status atualizado dos estágios
        """
        self.client.login(username='coordenador@test.com', password='senha123')
        
        # DADO que existem estágios cadastrados (setUp)
        
        # QUANDO o usuário acessar o painel
        response = self.client.get(reverse('painel_estagios'))
        
        # ENTÃO deve visualizar o status atualizado dos estágios
        self.assertEqual(response.status_code, 200)
        self.assertIn('estagios', response.context)
        
        # Verifica que os estágios estão sendo exibidos
        estagios = response.context['estagios']
        self.assertEqual(estagios.count(), 3)


class PainelEstagiosViewCA2Test(PainelEstagiosViewBaseTest):
    """
    Testes para CA2 - O sistema deve permitir a atualização automática das informações.
    
    US: Visualização em painel dos status dos estágios
    """
    
    def test_ca2_api_painel_retorna_json(self):
        """CA2 - Testa que API do painel retorna dados JSON"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_ca2_api_painel_inclui_timestamp(self):
        """CA2 - Testa que API inclui timestamp para controle de atualização"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('timestamp', data)
    
    def test_ca2_api_painel_inclui_estatisticas(self):
        """CA2 - Testa que API inclui estatísticas para atualização"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('estatisticas', data)
        self.assertEqual(data['estatisticas']['total'], 3)
    
    def test_ca2_api_estatisticas_estagios(self):
        """CA2 - Testa API específica de estatísticas"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_estatisticas_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('timestamp', data)
        self.assertIn('total', data)
        self.assertIn('analise', data)
        self.assertIn('em_andamento', data)
        self.assertIn('aprovado', data)
        self.assertIn('reprovado', data)
    
    def test_ca2_api_painel_inclui_estagios_por_status(self):
        """CA2 - Testa que API inclui estágios agrupados por status"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('estagios_por_status', data)
        self.assertIn('analise', data['estagios_por_status'])
        self.assertIn('em_andamento', data['estagios_por_status'])
    
    def test_ca2_api_atualizacao_reflete_mudancas(self):
        """CA2 - Testa que API reflete mudanças em tempo real"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        # Primeira chamada
        response1 = self.client.get(reverse('api_estatisticas_estagios'))
        data1 = response1.json()
        total_inicial = data1['total']
        
        # Cria novo estágio
        Estagio.objects.create(
            titulo="Novo Estágio",
            cargo="Estagiário",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='analise',
            aluno_solicitante=self.aluno
        )
        
        # Segunda chamada
        response2 = self.client.get(reverse('api_estatisticas_estagios'))
        data2 = response2.json()
        
        # Verifica que refletiu a mudança
        self.assertEqual(data2['total'], total_inicial + 1)


class PainelEstagiosViewCA3Test(PainelEstagiosViewBaseTest):
    """
    Testes para CA3 - O sistema deve ter acesso restrito conforme perfil do usuário.
    
    US: Visualização em painel dos status dos estágios
    """
    
    def test_ca3_acesso_requer_login(self):
        """CA3 - Testa que acesso ao painel requer autenticação"""
        response = self.client.get(reverse('painel_estagios'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_ca3_coordenador_ve_todos_estagios(self):
        """CA3 - Testa que coordenador visualiza todos os estágios"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        estatisticas = response.context['estatisticas']
        
        # Coordenador deve ver todos os 3 estágios
        self.assertEqual(estatisticas['total'], 3)
    
    def test_ca3_supervisor_ve_apenas_seus_estagios(self):
        """CA3 - Testa que supervisor visualiza apenas estágios que supervisiona"""
        # Cria outro supervisor
        outro_usuario = Usuario.objects.create_user(
            username='outro_supervisor@test.com',
            email='outro_supervisor@test.com',
            password='senha123',
            tipo='supervisor'
        )
        outro_supervisor = Supervisor.objects.create(
            usuario=outro_usuario,
            nome="Outro Supervisor",
            contato="11966666666",
            cargo="Coordenador",
            empresa=self.empresa
        )
        
        # Cria estágio com outro supervisor
        Estagio.objects.create(
            titulo="Estágio Outro Supervisor",
            cargo="Dev",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=outro_supervisor,
            status='analise'
        )
        
        # Login como supervisor original
        self.client.login(username='supervisor@test.com', password='senha123')
        
        response = self.client.get(reverse('painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        estatisticas = response.context['estatisticas']
        
        # Supervisor deve ver apenas os 3 estágios que supervisiona
        self.assertEqual(estatisticas['total'], 3)
    
    def test_ca3_aluno_ve_apenas_seus_estagios(self):
        """CA3 - Testa que aluno visualiza apenas seus próprios estágios"""
        # Cria outro aluno
        outro_usuario = Usuario.objects.create_user(
            username='outro_aluno@test.com',
            email='outro_aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        outro_aluno = Aluno.objects.create(
            nome="Outro Aluno",
            contato="11955555555",
            matricula="20240002",
            usuario=outro_usuario,
            instituicao=self.instituicao
        )
        
        # Cria estágio do outro aluno
        Estagio.objects.create(
            titulo="Estágio Outro Aluno",
            cargo="Dev",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='analise',
            aluno_solicitante=outro_aluno
        )
        
        # Login como aluno original
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        estatisticas = response.context['estatisticas']
        
        # Aluno deve ver apenas os 3 estágios dele
        self.assertEqual(estatisticas['total'], 3)
    
    def test_ca3_api_respeita_perfil_coordenador(self):
        """CA3 - Testa que API respeita perfil do coordenador"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Coordenador deve ver todos
        self.assertEqual(data['total_estagios'], 3)
    
    def test_ca3_api_respeita_perfil_aluno(self):
        """CA3 - Testa que API respeita perfil do aluno"""
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('api_painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Aluno vê apenas seus estágios
        self.assertEqual(data['total_estagios'], 3)
    
    def test_ca3_perfil_usuario_no_contexto(self):
        """CA3 - Testa que perfil do usuário está no contexto"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('painel_estagios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('perfil_usuario', response.context)
        self.assertEqual(response.context['perfil_usuario'], 'coordenador')


class FiltrarEstagiosPorPerfilTest(TestCase):
    """
    Testes unitários para a função _filtrar_estagios_por_perfil.
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Instituição",
            contato="111111",
            numero=1,
            bairro="Bairro",
            rua="Rua"
        )
        self.empresa = Empresa.objects.create(
            razao_social="Empresa",
            cnpj="12345678901234",
            numero=1,
            bairro="Bairro",
            rua="Rua"
        )
    
    def test_perfil_nao_reconhecido_retorna_vazio(self):
        """Testa que perfil não reconhecido não vê estágios"""
        from estagio.views import _filtrar_estagios_por_perfil
        
        # Cria usuário com tipo não padrão
        usuario = Usuario.objects.create_user(
            username='teste@test.com',
            email='teste@test.com',
            password='senha123',
            tipo='outro_tipo'
        )
        
        estagios = _filtrar_estagios_por_perfil(usuario)
        
        self.assertEqual(estagios.count(), 0)
    
    def test_supervisor_sem_registro_retorna_vazio(self):
        """Testa que supervisor sem registro Supervisor não vê estágios"""
        from estagio.views import _filtrar_estagios_por_perfil
        
        # Cria usuário supervisor sem registro Supervisor
        usuario = Usuario.objects.create_user(
            username='supervisor_sem@test.com',
            email='supervisor_sem@test.com',
            password='senha123',
            tipo='supervisor'
        )
        
        estagios = _filtrar_estagios_por_perfil(usuario)
        
        self.assertEqual(estagios.count(), 0)
    
    def test_aluno_sem_registro_retorna_vazio(self):
        """Testa que aluno sem registro Aluno não vê estágios"""
        from estagio.views import _filtrar_estagios_por_perfil
        
        # Cria usuário aluno sem registro Aluno
        usuario = Usuario.objects.create_user(
            username='aluno_sem@test.com',
            email='aluno_sem@test.com',
            password='senha123',
            tipo='aluno'
        )
        
        estagios = _filtrar_estagios_por_perfil(usuario)
        
        self.assertEqual(estagios.count(), 0)


class CalcularEstatisticasEstagiosTest(TestCase):
    """
    Testes unitários para a função _calcular_estatisticas_estagios.
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Instituição",
            contato="111111",
            numero=1,
            bairro="Bairro",
            rua="Rua"
        )
        self.empresa = Empresa.objects.create(
            razao_social="Empresa",
            cnpj="12345678901234",
            numero=1,
            bairro="Bairro",
            rua="Rua"
        )
        self.usuario_supervisor = Usuario.objects.create_user(
            username='sup@test.com',
            email='sup@test.com',
            password='senha123',
            tipo='supervisor'
        )
        self.supervisor = Supervisor.objects.create(
            usuario=self.usuario_supervisor,
            nome="Supervisor",
            contato="11999999999",
            cargo="Gerente",
            empresa=self.empresa
        )
    
    def test_estatisticas_sem_estagios(self):
        """Testa estatísticas quando não há estágios"""
        from estagio.views import _calcular_estatisticas_estagios
        
        estagios = Estagio.objects.none()
        estatisticas = _calcular_estatisticas_estagios(estagios)
        
        self.assertEqual(estatisticas['total'], 0)
        self.assertEqual(estatisticas['percentual_analise'], 0)
        self.assertEqual(estatisticas['percentual_aprovado'], 0)
    
    def test_estatisticas_com_estagios(self):
        """Testa cálculo de estatísticas com estágios"""
        from estagio.views import _calcular_estatisticas_estagios
        
        # Cria 4 estágios: 2 analise, 1 aprovado, 1 reprovado
        for i in range(2):
            Estagio.objects.create(
                titulo=f"Estágio Análise {i}",
                cargo="Dev",
                data_inicio=date.today(),
                data_fim=date.today() + timedelta(days=180),
                carga_horaria=20,
                empresa=self.empresa,
                supervisor=self.supervisor,
                status='analise'
            )
        
        Estagio.objects.create(
            titulo="Estágio Aprovado",
            cargo="Dev",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='aprovado'
        )
        
        Estagio.objects.create(
            titulo="Estágio Reprovado",
            cargo="Dev",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='reprovado'
        )
        
        estagios = Estagio.objects.all()
        estatisticas = _calcular_estatisticas_estagios(estagios)
        
        self.assertEqual(estatisticas['total'], 4)
        self.assertEqual(estatisticas['analise'], 2)
        self.assertEqual(estatisticas['aprovado'], 1)
        self.assertEqual(estatisticas['reprovado'], 1)
        self.assertEqual(estatisticas['percentual_analise'], 50.0)
        self.assertEqual(estatisticas['percentual_aprovado'], 25.0)


# ==================== TESTES DE MONITORAMENTO DE PENDÊNCIAS E RESULTADOS ====================

class MonitoramentoPendenciasBaseTest(TestCase):
    """
    Classe base com setup comum para testes de monitoramento de pendências.
    """
    
    def setUp(self):
        self.client = Client()
        
        # Cria instituição
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        # Cria empresa
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste",
            cnpj="98765432109876",
            numero=456,
            bairro="Centro",
            rua="Av Teste"
        )
        
        # Cria usuário coordenador
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
        )
        self.coordenador = CursoCoordenador.objects.create(
            usuario=self.usuario_coordenador,
            nome="Coordenador Teste",
            contato="11977777777",
            instituicao=self.instituicao
        )
        
        # Cria usuário supervisor
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
        
        # Cria usuário aluno
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@test.com',
            email='aluno@test.com',
            password='senha123',
            tipo='aluno'
        )
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            contato="11999999999",
            matricula="20240001",
            usuario=self.usuario_aluno,
            instituicao=self.instituicao
        )
        
        # Cria estágio
        self.estagio = Estagio.objects.create(
            titulo="Estágio Teste",
            cargo="Estagiário",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='em_andamento',
            aluno_solicitante=self.aluno
        )
        
        # Vincula aluno ao estágio
        self.aluno.estagio = self.estagio
        self.aluno.save()


class MonitoramentoPendenciasViewCA4Test(MonitoramentoPendenciasBaseTest):
    """
    Testes para CA4 - O sistema deve permitir a exibição de pendências por tipo.
    
    US: Monitoramento de pendências e resultados
    
    BDD:
    DADO que há pendências e resultados registrados
    QUANDO o usuário acessar o monitoramento
    ENTÃO deve visualizar alertas e resultados consolidados
    """
    
    def test_ca4_acesso_requer_login(self):
        """CA4 - Testa que acesso ao monitoramento requer autenticação"""
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_ca4_exibir_pendencias_por_tipo(self):
        """CA4 - Testa exibição de pendências agrupadas por tipo"""
        # Cria estágio em análise (pendência)
        Estagio.objects.create(
            titulo="Estágio Análise",
            cargo="Dev",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='analise',
            aluno_solicitante=self.aluno
        )
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('pendencias_por_tipo', response.context)
    
    def test_ca4_filtro_por_tipo_pendencia(self):
        """CA4 - Testa filtro de pendências por tipo específico"""
        # Cria estágio em análise
        Estagio.objects.create(
            titulo="Estágio Análise",
            cargo="Dev",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='analise',
            aluno_solicitante=self.aluno
        )
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'), {'tipo': 'estagio_analise'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['filtro_tipo'], 'estagio_analise')
    
    def test_ca4_api_pendencias_por_tipo(self):
        """CA4 - Testa API para obter pendências por tipo"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_pendencias_por_tipo', args=['estagio_analise']))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('tipo', data)
        self.assertIn('tipo_info', data)
        self.assertIn('pendencias', data)
    
    def test_ca4_api_tipo_invalido_retorna_erro(self):
        """CA4 - Testa que API retorna erro para tipo inválido"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_pendencias_por_tipo', args=['tipo_invalido']))
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_ca4_tipos_pendencia_disponiveis(self):
        """CA4 - Testa que tipos de pendência estão disponíveis no contexto"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('tipos_pendencia', response.context)
        
        tipos = response.context['tipos_pendencia']
        self.assertIn('documento_pendente', tipos)
        self.assertIn('documento_ajuste', tipos)
        self.assertIn('estagio_analise', tipos)


class MonitoramentoPendenciasViewCA5Test(MonitoramentoPendenciasBaseTest):
    """
    Testes para CA5 - O sistema deve ter um destaque visual para pendências críticas.
    
    US: Monitoramento de pendências e resultados
    """
    
    def test_ca5_identificar_pendencias_criticas(self):
        """CA5 - Testa identificação de pendências críticas"""
        # Cria documento com ajustes solicitados (crítico)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_critico.pdf",
            tipo="termo_compromisso",
            status='ajustes_solicitados',
            enviado_por=self.usuario_aluno
        )
        
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('pendencias_criticas', response.context)
        self.assertIn('total_criticas', response.context)
    
    def test_ca5_filtro_apenas_criticas(self):
        """CA5 - Testa filtro para exibir apenas pendências críticas"""
        # Cria documento com ajustes (crítico)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_critico.pdf",
            tipo="termo",
            status='ajustes_solicitados',
            enviado_por=self.usuario_aluno
        )
        
        self.client.login(username='aluno@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'), {'critico': 'true'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['filtro_critico'], 'true')
    
    def test_ca5_documento_prazo_proximo_e_critico(self):
        """CA5 - Testa que documento com prazo próximo é marcado como crítico"""
        # Cria documento com prazo em 2 dias (crítico)
        prazo = date.today() + timedelta(days=2)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc_prazo.pdf",
            tipo="termo",
            status='enviado',
            prazo_limite=prazo,
            enviado_por=self.usuario_aluno
        )
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        pendencias_criticas = response.context['pendencias_criticas']
        
        # Deve haver pelo menos uma pendência crítica de documento com prazo
        self.assertTrue(
            any(p['tipo'] == 'documento_prazo' for p in pendencias_criticas)
        )
    
    def test_ca5_api_retorna_pendencias_criticas(self):
        """CA5 - Testa que API retorna informações de pendências críticas"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('total_criticas', data)
        self.assertIn('pendencias_criticas', data)


class MonitoramentoPendenciasViewCA6Test(MonitoramentoPendenciasBaseTest):
    """
    Testes para CA6 - O sistema deve permitir a visualização de resultados consolidados.
    
    US: Monitoramento de pendências e resultados
    
    BDD:
    DADO que há pendências e resultados registrados
    QUANDO o usuário acessar o monitoramento
    ENTÃO deve visualizar alertas e resultados consolidados
    """
    
    def test_ca6_resultados_consolidados_no_contexto(self):
        """CA6 - Testa que resultados consolidados estão no contexto"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('resultados_consolidados', response.context)
        
        resultados = response.context['resultados_consolidados']
        self.assertIn('estagios', resultados)
        self.assertIn('documentos', resultados)
        self.assertIn('avaliacoes', resultados)
        self.assertIn('horas', resultados)
    
    def test_ca6_consolidacao_estagios(self):
        """CA6 - Testa consolidação de dados de estágios"""
        # Cria mais estágios com diferentes status
        Estagio.objects.create(
            titulo="Estágio Aprovado",
            cargo="Dev",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='aprovado'
        )
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        resultados = response.context['resultados_consolidados']
        
        self.assertIn('total', resultados['estagios'])
        self.assertIn('em_andamento', resultados['estagios'])
        self.assertIn('aprovados', resultados['estagios'])
    
    def test_ca6_consolidacao_documentos(self):
        """CA6 - Testa consolidação de dados de documentos"""
        # Cria documentos
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="doc1.pdf",
            tipo="termo",
            status='aprovado',
            enviado_por=self.usuario_aluno
        )
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        resultados = response.context['resultados_consolidados']
        
        self.assertIn('total', resultados['documentos'])
        self.assertIn('aprovados', resultados['documentos'])
        self.assertIn('pendentes', resultados['documentos'])
    
    def test_ca6_consolidacao_horas(self):
        """CA6 - Testa consolidação de horas cumpridas"""
        # Registra horas
        HorasCumpridas.objects.create(
            aluno=self.aluno,
            data=date.today(),
            quantidade=8,
            descricao="Atividades do dia"
        )
        HorasCumpridas.objects.create(
            aluno=self.aluno,
            data=date.today() - timedelta(days=1),
            quantidade=6,
            descricao="Atividades ontem"
        )
        
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        resultados = response.context['resultados_consolidados']
        
        self.assertEqual(resultados['horas']['total_registros'], 2)
        self.assertEqual(resultados['horas']['total_horas'], 14)
    
    def test_ca6_api_resultados_consolidados(self):
        """CA6 - Testa API específica de resultados consolidados"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_resultados_consolidados'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('timestamp', data)
        self.assertIn('estagios', data)
        self.assertIn('documentos', data)
        self.assertIn('avaliacoes', data)
        self.assertIn('horas', data)
    
    def test_ca6_bdd_visualizar_alertas_e_resultados(self):
        """
        BDD: DADO que há pendências e resultados registrados
             QUANDO o usuário acessar o monitoramento
             ENTÃO deve visualizar alertas e resultados consolidados
        """
        # DADO que há pendências e resultados registrados
        # Cria estágio em análise (pendência)
        Estagio.objects.create(
            titulo="Estágio Análise",
            cargo="Dev",
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=180),
            carga_horaria=20,
            empresa=self.empresa,
            supervisor=self.supervisor,
            status='analise',
            aluno_solicitante=self.aluno
        )
        
        # Cria documento com prazo próximo (pendência crítica)
        Documento.objects.create(
            estagio=self.estagio,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            data_envio=date.today(),
            versao=1.0,
            nome_arquivo="termo.pdf",
            tipo="termo",
            status='enviado',
            prazo_limite=date.today() + timedelta(days=2),
            enviado_por=self.usuario_aluno
        )
        
        # Registra horas (resultado)
        HorasCumpridas.objects.create(
            aluno=self.aluno,
            data=date.today(),
            quantidade=8,
            descricao="Trabalho"
        )
        
        # QUANDO o usuário acessar o monitoramento
        self.client.login(username='coordenador@test.com', password='senha123')
        response = self.client.get(reverse('monitoramento_pendencias'))
        
        # ENTÃO deve visualizar alertas e resultados consolidados
        self.assertEqual(response.status_code, 200)
        
        # Verifica alertas (pendências)
        self.assertIn('pendencias', response.context)
        self.assertIn('pendencias_criticas', response.context)
        self.assertGreater(response.context['total_pendencias'], 0)
        
        # Verifica resultados consolidados
        resultados = response.context['resultados_consolidados']
        self.assertGreater(resultados['estagios']['total'], 0)
        self.assertGreater(resultados['horas']['total_horas'], 0)


class ApiMonitoramentoPendenciasTest(MonitoramentoPendenciasBaseTest):
    """
    Testes para as APIs de monitoramento de pendências.
    """
    
    def test_api_monitoramento_retorna_json(self):
        """Testa que API retorna JSON válido"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_api_monitoramento_inclui_timestamp(self):
        """Testa que API inclui timestamp"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('timestamp', data)
    
    def test_api_monitoramento_estrutura_completa(self):
        """Testa estrutura completa da resposta da API"""
        self.client.login(username='coordenador@test.com', password='senha123')
        
        response = self.client.get(reverse('api_monitoramento_pendencias'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('total_pendencias', data)
        self.assertIn('total_criticas', data)
        self.assertIn('pendencias_por_tipo', data)
        self.assertIn('pendencias_criticas', data)
        self.assertIn('resultados_consolidados', data)


class FuncoesAuxiliaresMonitoramentoTest(TestCase):
    """
    Testes unitários para funções auxiliares de monitoramento.
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Instituição",
            contato="111111",
            numero=1,
            bairro="Bairro",
            rua="Rua"
        )
        self.empresa = Empresa.objects.create(
            razao_social="Empresa",
            cnpj="12345678901234",
            numero=1,
            bairro="Bairro",
            rua="Rua"
        )
    
    def test_agrupar_pendencias_por_tipo(self):
        """Testa agrupamento de pendências por tipo"""
        from estagio.views import _agrupar_pendencias_por_tipo
        
        pendencias = [
            {'tipo': 'documento_pendente', 'titulo': 'Doc 1', 'critico': False},
            {'tipo': 'documento_pendente', 'titulo': 'Doc 2', 'critico': False},
            {'tipo': 'estagio_analise', 'titulo': 'Estágio 1', 'critico': False},
        ]
        
        agrupadas = _agrupar_pendencias_por_tipo(pendencias)
        
        self.assertEqual(len(agrupadas['documento_pendente']), 2)
        self.assertEqual(len(agrupadas['estagio_analise']), 1)
    
    def test_filtrar_pendencias_criticas(self):
        """Testa filtro de pendências críticas"""
        from estagio.views import _filtrar_pendencias_criticas
        
        pendencias = [
            {'tipo': 'documento_pendente', 'titulo': 'Doc 1', 'critico': False},
            {'tipo': 'documento_ajuste', 'titulo': 'Doc 2', 'critico': True},
            {'tipo': 'documento_prazo', 'titulo': 'Doc 3', 'critico': True},
        ]
        
        criticas = _filtrar_pendencias_criticas(pendencias)
        
        self.assertEqual(len(criticas), 2)
        self.assertTrue(all(p['critico'] for p in criticas))
    
    def test_obter_pendencias_perfil_desconhecido(self):
        """Testa que perfil desconhecido retorna lista vazia"""
        from estagio.views import _obter_pendencias_por_perfil
        
        usuario = Usuario.objects.create_user(
            username='outro@test.com',
            email='outro@test.com',
            password='senha123',
            tipo='outro'
        )
        
        pendencias = _obter_pendencias_por_perfil(usuario)
        
        self.assertEqual(len(pendencias), 0)
    
    def test_consolidar_resultados_sem_dados(self):
        """Testa consolidação quando não há dados"""
        from estagio.views import _consolidar_resultados
        
        usuario = Usuario.objects.create_user(
            username='coord@test.com',
            email='coord@test.com',
            password='senha123',
            tipo='coordenador'
        )
        CursoCoordenador.objects.create(
            usuario=usuario,
            nome="Coord",
            contato="111111",
            instituicao=self.instituicao
        )
        
        resultados = _consolidar_resultados(usuario)
        
        self.assertEqual(resultados['estagios']['total'], 0)
        self.assertEqual(resultados['documentos']['total'], 0)
        self.assertEqual(resultados['horas']['total_horas'], 0)


# =============================================================================
# Testes de Geração de Relatórios de Estágios
# US: Geração de relatórios dos estágios
# BDD: DADO que existem dados de estágios
#      QUANDO o usuário solicitar um relatório
#      ENTÃO o sistema deve gerar o relatório conforme filtros aplicados
# =============================================================================

class RelatorioEstagiosBaseTest(TestCase):
    """
    Classe base com setup comum para testes de relatórios.
    """
    
    def setUp(self):
        self.client = Client()
        
        # Criar instituição
        self.instituicao = Instituicao.objects.create(
            nome="Instituição Teste Relatório",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        # Criar empresa
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste Relatório",
            cnpj="12345678901234",
            numero=456,
            bairro="Bairro Comercial",
            rua="Av Comercial"
        )
        
        self.empresa2 = Empresa.objects.create(
            razao_social="Segunda Empresa",
            cnpj="98765432101234",
            numero=789,
            bairro="Bairro Industrial",
            rua="Av Industrial"
        )
        
        # Criar usuário supervisor
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor_rel@test.com',
            email='supervisor_rel@test.com',
            password='senha123',
            tipo='supervisor'
        )
        self.supervisor = Supervisor.objects.create(
            usuario=self.usuario_supervisor,
            nome="Supervisor Relatório",
            contato="11988887777",
            cargo="Gerente",
            empresa=self.empresa
        )
        
        # Criar usuário coordenador
        self.usuario_coordenador = Usuario.objects.create_user(
            username='coordenador_rel@test.com',
            email='coordenador_rel@test.com',
            password='senha123',
            tipo='coordenador'
        )
        self.coordenador = CursoCoordenador.objects.create(
            usuario=self.usuario_coordenador,
            nome="Coordenador Relatório",
            contato="11999998888",
            instituicao=self.instituicao
        )
        
        # Criar usuário aluno
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno_rel@test.com',
            email='aluno_rel@test.com',
            password='senha123',
            tipo='aluno'
        )
        self.aluno = Aluno.objects.create(
            usuario=self.usuario_aluno,
            nome="Aluno Relatório",
            contato="aluno_rel@email.com",
            matricula="20231234",
            instituicao=self.instituicao
        )
        
        # Criar estágios para testes
        self.estagio1 = Estagio.objects.create(
            titulo="Estágio Desenvolvimento",
            cargo="Desenvolvedor Jr",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=120),
            carga_horaria=20,
            status='em_andamento',
            aluno_solicitante=self.aluno
        )
        
        self.estagio2 = Estagio.objects.create(
            titulo="Estágio Suporte",
            cargo="Analista Suporte",
            empresa=self.empresa2,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=150),
            carga_horaria=30,
            status='aprovado',
            aluno_solicitante=self.aluno
        )
        
        self.estagio3 = Estagio.objects.create(
            titulo="Estágio Análise",
            cargo="Analista Jr",
            empresa=self.empresa,
            supervisor=self.supervisor,
            data_inicio=date.today() - timedelta(days=90),
            data_fim=date.today() + timedelta(days=90),
            carga_horaria=25,
            status='analise'
        )


class RelatorioEstagiosFormCA1Test(RelatorioEstagiosBaseTest):
    """
    Testes para CA1 - O sistema deve permitir a geração de relatório com filtros configuráveis
    """
    
    def test_form_aceita_filtro_status(self):
        """CA1 - Verifica que o formulário aceita filtro por status"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'status': 'em_andamento',
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'em_andamento')
    
    def test_form_aceita_filtro_empresa(self):
        """CA1 - Verifica que o formulário aceita filtro por empresa"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'empresa': self.empresa.id,
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['empresa'], self.empresa)
    
    def test_form_aceita_filtro_supervisor(self):
        """CA1 - Verifica que o formulário aceita filtro por supervisor"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'supervisor': self.supervisor.id,
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['supervisor'], self.supervisor)
    
    def test_form_aceita_filtro_instituicao(self):
        """CA1 - Verifica que o formulário aceita filtro por instituição"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'instituicao': self.instituicao.id,
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['instituicao'], self.instituicao)
    
    def test_form_aceita_multiplos_filtros(self):
        """CA1 - Verifica que o formulário aceita múltiplos filtros simultaneamente"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'status': 'aprovado',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        filtros_ativos = form.get_filtros_ativos()
        self.assertIn('status', filtros_ativos)
        self.assertIn('empresa', filtros_ativos)
        self.assertIn('supervisor', filtros_ativos)
    
    def test_api_relatorio_com_filtro_status(self):
        """CA1 - Verifica API aplica filtro de status"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {'status': 'em_andamento'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verifica que só retornou estágios em andamento
        for estagio in data['relatorio']['estagios']:
            self.assertEqual(estagio['status'], 'em_andamento')
    
    def test_api_relatorio_com_filtro_empresa(self):
        """CA1 - Verifica API aplica filtro de empresa"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {'empresa': self.empresa.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verifica que só retornou estágios da empresa filtrada
        for estagio in data['relatorio']['estagios']:
            self.assertEqual(estagio['empresa']['razao_social'], self.empresa.razao_social)


class RelatorioEstagiosFormCA2Test(RelatorioEstagiosBaseTest):
    """
    Testes para CA2 - O sistema deve permitir a inclusão de dados completos do estágio
    """
    
    def test_form_aceita_opcoes_inclusao(self):
        """CA2 - Verifica opções de inclusão de dados"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'incluir_documentos': True,
            'incluir_avaliacoes': True,
            'incluir_horas': True,
            'incluir_aluno': True,
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        opcoes = form.get_opcoes_inclusao()
        self.assertTrue(opcoes['documentos'])
        self.assertTrue(opcoes['avaliacoes'])
        self.assertTrue(opcoes['horas'])
        self.assertTrue(opcoes['aluno'])
    
    def test_relatorio_inclui_dados_estagio_completos(self):
        """CA2 - Verifica que relatório inclui dados completos do estágio"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {'incluir_aluno': 'true', 'incluir_documentos': 'true'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verifica dados básicos do estágio
        estagio = data['relatorio']['estagios'][0]
        self.assertIn('id', estagio)
        self.assertIn('titulo', estagio)
        self.assertIn('cargo', estagio)
        self.assertIn('status', estagio)
        self.assertIn('status_display', estagio)
        self.assertIn('data_inicio', estagio)
        self.assertIn('data_fim', estagio)
        self.assertIn('carga_horaria', estagio)
        self.assertIn('empresa', estagio)
        self.assertIn('supervisor', estagio)
    
    def test_relatorio_inclui_dados_empresa(self):
        """CA2 - Verifica que relatório inclui dados da empresa"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(reverse('api_relatorio_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        estagio = data['relatorio']['estagios'][0]
        self.assertIn('razao_social', estagio['empresa'])
        self.assertIn('cnpj', estagio['empresa'])
    
    def test_relatorio_inclui_dados_supervisor(self):
        """CA2 - Verifica que relatório inclui dados do supervisor"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(reverse('api_relatorio_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        estagio = data['relatorio']['estagios'][0]
        self.assertIn('nome', estagio['supervisor'])
        self.assertIn('cargo', estagio['supervisor'])
    
    def test_relatorio_inclui_dados_aluno(self):
        """CA2 - Verifica que relatório inclui dados do aluno quando solicitado"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {'incluir_aluno': 'true'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Encontra um estágio com aluno
        for estagio in data['relatorio']['estagios']:
            if 'aluno' in estagio:
                self.assertIn('nome', estagio['aluno'])
                self.assertIn('matricula', estagio['aluno'])
                self.assertIn('contato', estagio['aluno'])
                break
    
    def test_relatorio_inclui_documentos(self):
        """CA2 - Verifica que relatório inclui documentos quando solicitado"""
        # Criar documento
        Documento.objects.create(
            nome_arquivo='termo.pdf',
            tipo='termo_compromisso',
            data_envio=date.today(),
            versao=1.0,
            arquivo='documentos/termo.pdf',
            estagio=self.estagio1,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            status='aprovado'
        )
        
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {'incluir_documentos': 'true'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Encontra estágio com documentos
        for estagio in data['relatorio']['estagios']:
            if 'documentos' in estagio:
                self.assertIn('total', estagio['documentos'])
                self.assertIn('aprovados', estagio['documentos'])
                self.assertIn('pendentes', estagio['documentos'])
                break
    
    def test_relatorio_inclui_horas(self):
        """CA2 - Verifica que relatório inclui horas quando solicitado"""
        # Criar registro de horas
        HorasCumpridas.objects.create(
            aluno=self.aluno,
            data=date.today() - timedelta(days=5),
            quantidade=8,
            descricao='Desenvolvimento'
        )
        
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {'incluir_horas': 'true'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Encontra estágio com horas
        for estagio in data['relatorio']['estagios']:
            if 'horas' in estagio:
                self.assertIn('total_registros', estagio['horas'])
                self.assertIn('total_horas', estagio['horas'])
                break
    
    def test_relatorio_inclui_resumo(self):
        """CA2 - Verifica que relatório inclui resumo consolidado"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(reverse('api_relatorio_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        resumo = data['relatorio']['resumo']
        self.assertIn('total', resumo)
        self.assertIn('por_status', resumo)
        self.assertIn('por_empresa', resumo)


class RelatorioEstagiosFormCA3Test(RelatorioEstagiosBaseTest):
    """
    Testes para CA3 - O sistema deve permitir a validação de período para geração
    """
    
    def test_form_valida_periodo_completo(self):
        """CA3 - Verifica que período requer ambas as datas"""
        from estagio.forms import RelatorioEstagiosForm
        
        # Apenas data início - deve falhar
        form_data = {
            'data_inicio': date.today() - timedelta(days=30),
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('data_fim', form.errors)
    
    def test_form_valida_periodo_data_fim_obrigatoria(self):
        """CA3 - Verifica que data_fim requer data_inicio"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'data_fim': date.today(),
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('data_inicio', form.errors)
    
    def test_form_valida_data_fim_maior_que_inicio(self):
        """CA3 - Verifica que data_fim não pode ser anterior à data_inicio"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'data_inicio': date.today(),
            'data_fim': date.today() - timedelta(days=10),
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('data_fim', form.errors)
    
    def test_form_valida_periodo_maximo_365_dias(self):
        """CA3 - Verifica limite máximo de período de 365 dias"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'data_inicio': date.today() - timedelta(days=400),
            'data_fim': date.today() - timedelta(days=1),
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('data_fim', form.errors)
        self.assertIn('365 dias', str(form.errors['data_fim']))
    
    def test_form_valida_data_fim_nao_futura(self):
        """CA3 - Verifica que data_fim não pode ser futura"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'data_inicio': date.today() - timedelta(days=30),
            'data_fim': date.today() + timedelta(days=10),
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('data_fim', form.errors)
    
    def test_form_aceita_periodo_valido(self):
        """CA3 - Verifica que período válido é aceito"""
        from estagio.forms import RelatorioEstagiosForm
        
        form_data = {
            'data_inicio': date.today() - timedelta(days=60),
            'data_fim': date.today() - timedelta(days=1),
        }
        form = RelatorioEstagiosForm(data=form_data)
        
        self.assertTrue(form.is_valid())
    
    def test_api_valida_periodo_invalido(self):
        """CA3 - Verifica que API rejeita período inválido"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {
                'data_inicio': (date.today()).isoformat(),
                'data_fim': (date.today() - timedelta(days=10)).isoformat(),
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('errors', data)
    
    def test_api_filtra_por_periodo(self):
        """CA3 - Verifica que API filtra corretamente por período"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        # Filtrar por período que inclui estagio1 (60 dias atrás)
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {
                'data_inicio': (date.today() - timedelta(days=70)).isoformat(),
                'data_fim': (date.today() - timedelta(days=50)).isoformat(),
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_funcao_auxiliar_validar_periodo(self):
        """CA3 - Testa função auxiliar de validação de período"""
        from estagio.views import validar_periodo_relatorio
        
        # Período válido
        valid, error = validar_periodo_relatorio(
            date.today() - timedelta(days=30),
            date.today() - timedelta(days=1)
        )
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        # Período inválido - fim antes do início
        valid, error = validar_periodo_relatorio(
            date.today(),
            date.today() - timedelta(days=10)
        )
        self.assertFalse(valid)
        self.assertIn('anterior', error)
        
        # Período inválido - mais de 365 dias
        valid, error = validar_periodo_relatorio(
            date.today() - timedelta(days=400),
            date.today() - timedelta(days=1)
        )
        self.assertFalse(valid)
        self.assertIn('365', error)


class RelatorioEstagiosBDDTest(RelatorioEstagiosBaseTest):
    """
    Testes BDD: DADO que existem dados de estágios
               QUANDO o usuário solicitar um relatório
               ENTÃO o sistema deve gerar o relatório conforme filtros aplicados
    """
    
    def test_bdd_coordenador_gera_relatorio_estagios(self):
        """
        BDD: Coordenador gera relatório de estágios
        DADO que existem estágios cadastrados
        QUANDO o coordenador solicita relatório
        ENTÃO recebe relatório com dados dos estágios
        """
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(reverse('api_relatorio_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('relatorio', data)
        self.assertIn('estagios', data['relatorio'])
        self.assertGreater(len(data['relatorio']['estagios']), 0)
    
    def test_bdd_coordenador_gera_relatorio_com_filtros(self):
        """
        BDD: Coordenador gera relatório com filtros
        DADO que existem estágios com diferentes status
        QUANDO o coordenador solicita relatório filtrando por status
        ENTÃO recebe apenas estágios com aquele status
        """
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {'status': 'aprovado'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verifica que todos os estágios têm status 'aprovado'
        for estagio in data['relatorio']['estagios']:
            self.assertEqual(estagio['status'], 'aprovado')
    
    def test_bdd_supervisor_gera_relatorio_seus_estagios(self):
        """
        BDD: Supervisor gera relatório de seus estágios
        DADO que existem estágios sob supervisão do supervisor
        QUANDO o supervisor solicita relatório
        ENTÃO recebe apenas estágios sob sua supervisão
        """
        self.client.login(username='supervisor_rel@test.com', password='senha123')
        
        response = self.client.get(reverse('api_relatorio_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verifica que todos os estágios são do supervisor logado
        for estagio in data['relatorio']['estagios']:
            self.assertEqual(estagio['supervisor']['nome'], self.supervisor.nome)
    
    def test_bdd_aluno_gera_relatorio_seus_estagios(self):
        """
        BDD: Aluno gera relatório de seus estágios
        DADO que aluno possui estágios vinculados
        QUANDO o aluno solicita relatório
        ENTÃO recebe apenas seus próprios estágios
        """
        self.client.login(username='aluno_rel@test.com', password='senha123')
        
        response = self.client.get(reverse('api_relatorio_estagios'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verifica que todos os estágios são do aluno logado
        for estagio in data['relatorio']['estagios']:
            if 'aluno' in estagio:
                self.assertEqual(estagio['aluno']['matricula'], self.aluno.matricula)
    
    def test_bdd_relatorio_inclui_dados_completos(self):
        """
        BDD: Relatório inclui dados completos
        DADO que existem estágios com documentos e horas
        QUANDO usuário solicita relatório com inclusão de dados
        ENTÃO relatório contém todos os dados solicitados
        """
        # Criar documento
        Documento.objects.create(
            nome_arquivo='termo_completo.pdf',
            tipo='termo_compromisso',
            data_envio=date.today(),
            versao=1.0,
            arquivo='documentos/termo_completo.pdf',
            estagio=self.estagio1,
            supervisor=self.supervisor,
            coordenador=self.coordenador,
            status='aprovado'
        )
        
        # Criar horas
        HorasCumpridas.objects.create(
            aluno=self.aluno,
            data=date.today() - timedelta(days=5),
            quantidade=8,
            descricao='Atividade 1'
        )
        
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_estagios'),
            {
                'incluir_documentos': 'true',
                'incluir_horas': 'true',
                'incluir_aluno': 'true',
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verifica dados completos
        self.assertIn('relatorio', data)
        self.assertIn('resumo', data['relatorio'])
        self.assertIn('data_geracao', data['relatorio'])


class RelatorioEstagiosViewTest(RelatorioEstagiosBaseTest):
    """
    Testes para a view principal de geração de relatórios.
    """
    
    def test_view_requer_autenticacao(self):
        """Verifica que view requer autenticação"""
        response = self.client.get(reverse('gerar_relatorio_estagios'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_view_get_renderiza_form(self):
        """Verifica que GET renderiza formulário"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(reverse('gerar_relatorio_estagios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_view_post_gera_relatorio(self):
        """Verifica que POST gera relatório"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.post(
            reverse('gerar_relatorio_estagios'),
            {'status': 'em_andamento'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('relatorio', response.context)
    
    def test_view_post_com_filtros_invalidos(self):
        """Verifica tratamento de filtros inválidos"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.post(
            reverse('gerar_relatorio_estagios'),
            {
                'data_inicio': date.today().isoformat(),
                # data_fim ausente - inválido
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('erros', response.context)


class ApiRelatorioExportarTest(RelatorioEstagiosBaseTest):
    """
    Testes para API de exportação de relatórios.
    """
    
    def test_exportar_json(self):
        """Testa exportação em formato JSON"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_exportar'),
            {'formato': 'json'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_exportar_csv(self):
        """Testa exportação em formato CSV"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_exportar'),
            {'formato': 'csv'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_exportar_com_filtros_invalidos_retorna_erro(self):
        """Verifica que exportação com filtros inválidos retorna erro"""
        self.client.login(username='coordenador_rel@test.com', password='senha123')
        
        response = self.client.get(
            reverse('api_relatorio_exportar'),
            {
                'data_inicio': date.today().isoformat(),
                # data_fim ausente - inválido
            }
        )
        
        self.assertEqual(response.status_code, 400)


class FuncoesAuxiliaresRelatorioTest(TestCase):
    """
    Testes unitários para funções auxiliares de relatórios.
    """
    
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome="Instituição Aux",
            contato="111111",
            numero=1,
            bairro="Bairro",
            rua="Rua"
        )
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Aux",
            cnpj="11111111111111",
            numero=1,
            bairro="Bairro",
            rua="Rua"
        )
    
    def test_obter_estagios_perfil_desconhecido(self):
        """Testa que perfil desconhecido retorna queryset vazio"""
        from estagio.views import _obter_estagios_por_perfil
        
        usuario = Usuario.objects.create_user(
            username='outro_rel@test.com',
            email='outro_rel@test.com',
            password='senha123',
            tipo='outro'
        )
        
        estagios = _obter_estagios_por_perfil(usuario)
        
        self.assertEqual(estagios.count(), 0)
    
    def test_aplicar_filtros_sem_dados(self):
        """Testa aplicação de filtros em queryset vazio"""
        from estagio.views import _aplicar_filtros_relatorio
        from estagio.models import Estagio
        
        estagios = Estagio.objects.none()
        filtros = {
            'status': 'aprovado',
            'data_inicio': date.today() - timedelta(days=30),
            'data_fim': date.today(),
        }
        
        resultado = _aplicar_filtros_relatorio(estagios, filtros)
        
        self.assertEqual(resultado.count(), 0)
    
    def test_validar_periodo_sem_datas(self):
        """Testa validação sem datas informadas"""
        from estagio.views import validar_periodo_relatorio
        
        valid, error = validar_periodo_relatorio(None, None)
        
        self.assertTrue(valid)
        self.assertIsNone(error)
