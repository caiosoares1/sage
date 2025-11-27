"""
Testes para os forms do sistema
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from estagio.forms import EstagioForm, DocumentoForm
from admin.models import Empresa, Supervisor, CursoCoordenador, Instituicao
from users.models import Usuario


class EstagioFormTest(TestCase):
    """Testes para o formulário de estágio"""
    
    def setUp(self):
        # Criar empresa
        self.empresa = Empresa.objects.create(
            razao_social="Empresa Teste",
            cnpj="98765432109876",
            numero=456,
            bairro="Centro",
            rua="Av Teste"
        )
        
        # Criar supervisor
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
    
    def test_form_valido(self):
        """Testa formulário com dados válidos"""
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today() + timedelta(days=7),
            'data_fim': date.today() + timedelta(days=90),
            'carga_horaria': 20
        }
        
        form = EstagioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_clean_data_inicio_passado(self):
        """Testa validação de data de início no passado"""
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today() - timedelta(days=1),  # Data passada
            'data_fim': date.today() + timedelta(days=90),
            'carga_horaria': 20
        }
        
        form = EstagioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('data_inicio', form.errors)
        self.assertIn('não pode ser anterior a hoje', str(form.errors['data_inicio']))
    
    def test_clean_data_inicio_hoje(self):
        """Testa que data de início pode ser hoje"""
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today(),
            'data_fim': date.today() + timedelta(days=90),
            'carga_horaria': 20
        }
        
        form = EstagioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_clean_data_fim_antes_inicio(self):
        """Testa validação de data de término antes da data de início"""
        data_inicio = date.today() + timedelta(days=7)
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': data_inicio,
            'data_fim': data_inicio - timedelta(days=1),  # Antes do início
            'carga_horaria': 20
        }
        
        form = EstagioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('data_fim', form.errors)
        self.assertIn('posterior à data de início', str(form.errors['data_fim']))
    
    def test_clean_data_fim_igual_inicio(self):
        """Testa validação de data de término igual à data de início"""
        data = date.today() + timedelta(days=7)
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': data,
            'data_fim': data,  # Mesma data
            'carga_horaria': 20
        }
        
        form = EstagioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('data_fim', form.errors)
    
    def test_clean_carga_horaria_menor_que_1(self):
        """Testa validação de carga horária menor que 1"""
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today() + timedelta(days=7),
            'data_fim': date.today() + timedelta(days=90),
            'carga_horaria': -5  # Valor negativo/inválido
        }
        
        form = EstagioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('carga_horaria', form.errors)
    
    def test_clean_carga_horaria_maior_que_40(self):
        """Testa validação de carga horária maior que 40"""
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today() + timedelta(days=7),
            'data_fim': date.today() + timedelta(days=90),
            'carga_horaria': 41  # Maior que 40
        }
        
        form = EstagioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('carga_horaria', form.errors)
        self.assertIn('entre 1 e 40', str(form.errors['carga_horaria']))
    
    def test_clean_carga_horaria_valida_limite_inferior(self):
        """Testa carga horária válida no limite inferior (1)"""
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today() + timedelta(days=7),
            'data_fim': date.today() + timedelta(days=90),
            'carga_horaria': 1
        }
        
        form = EstagioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_clean_carga_horaria_valida_limite_superior(self):
        """Testa carga horária válida no limite superior (40)"""
        form_data = {
            'titulo': 'Estágio em Desenvolvimento',
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today() + timedelta(days=7),
            'data_fim': date.today() + timedelta(days=90),
            'carga_horaria': 40
        }
        
        form = EstagioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_titulo_obrigatorio(self):
        """Testa que título é obrigatório"""
        form_data = {
            'cargo': 'Desenvolvedor Junior',
            'empresa': self.empresa.id,
            'supervisor': self.supervisor.id,
            'data_inicio': date.today() + timedelta(days=7),
            'data_fim': date.today() + timedelta(days=90),
            'carga_horaria': 20
        }
        
        form = EstagioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('titulo', form.errors)
    
    def test_campos_obrigatorios(self):
        """Testa que todos os campos obrigatórios estão presentes"""
        form = EstagioForm(data={})
        self.assertFalse(form.is_valid())
        
        campos_obrigatorios = ['titulo', 'cargo', 'empresa', 'supervisor', 
                               'data_inicio', 'data_fim', 'carga_horaria']
        for campo in campos_obrigatorios:
            self.assertIn(campo, form.errors)


class DocumentoFormTest(TestCase):
    """Testes para o formulário de documento"""
    
    def setUp(self):
        # Criar instituição
        self.instituicao = Instituicao.objects.create(
            nome="Universidade Teste",
            contato="1133334444",
            numero=123,
            bairro="Centro",
            rua="Rua Teste"
        )
        
        # Criar coordenador
        usuario_coordenador = Usuario.objects.create_user(
            username='coordenador@test.com',
            email='coordenador@test.com',
            password='senha123',
            tipo='coordenador'
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
    
    def test_form_valido_pdf(self):
        """Testa formulário com arquivo PDF válido"""
        arquivo = SimpleUploadedFile(
            "termo.pdf",
            b"conteudo do pdf",
            content_type="application/pdf"
        )
        
        form_data = {'coordenador': self.coordenador.id}
        form_files = {'arquivo': arquivo}
        
        form = DocumentoForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
    
    def test_form_valido_docx(self):
        """Testa formulário com arquivo DOCX válido"""
        arquivo = SimpleUploadedFile(
            "termo.docx",
            b"conteudo do docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        form_data = {'coordenador': self.coordenador.id}
        form_files = {'arquivo': arquivo}
        
        form = DocumentoForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
    
    def test_clean_arquivo_extensao_invalida(self):
        """Testa validação de arquivo com extensão inválida"""
        arquivo = SimpleUploadedFile(
            "termo.txt",
            b"conteudo do arquivo",
            content_type="text/plain"
        )
        
        form_data = {'coordenador': self.coordenador.id}
        form_files = {'arquivo': arquivo}
        
        form = DocumentoForm(data=form_data, files=form_files)
        self.assertFalse(form.is_valid())
        self.assertIn('arquivo', form.errors)
        self.assertIn('PDF ou DOCX', str(form.errors['arquivo']))
    
    def test_clean_arquivo_tamanho_excedido(self):
        """Testa validação de arquivo maior que 10MB"""
        # Criar arquivo de 11MB
        arquivo = SimpleUploadedFile(
            "termo.pdf",
            b"x" * (11 * 1024 * 1024),  # 11MB
            content_type="application/pdf"
        )
        
        form_data = {'coordenador': self.coordenador.id}
        form_files = {'arquivo': arquivo}
        
        form = DocumentoForm(data=form_data, files=form_files)
        self.assertFalse(form.is_valid())
        self.assertIn('arquivo', form.errors)
        self.assertIn('10MB', str(form.errors['arquivo']))
    
    def test_clean_arquivo_tamanho_limite(self):
        """Testa arquivo com tamanho no limite (10MB)"""
        # Criar arquivo de exatamente 10MB
        arquivo = SimpleUploadedFile(
            "termo.pdf",
            b"x" * (10 * 1024 * 1024),  # 10MB
            content_type="application/pdf"
        )
        
        form_data = {'coordenador': self.coordenador.id}
        form_files = {'arquivo': arquivo}
        
        form = DocumentoForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
    
    def test_coordenador_obrigatorio(self):
        """Testa que coordenador é obrigatório"""
        arquivo = SimpleUploadedFile(
            "termo.pdf",
            b"conteudo do pdf",
            content_type="application/pdf"
        )
        
        form_files = {'arquivo': arquivo}
        
        form = DocumentoForm(data={}, files=form_files)
        self.assertFalse(form.is_valid())
        self.assertIn('coordenador', form.errors)
    
    def test_arquivo_obrigatorio(self):
        """Testa que arquivo é obrigatório"""
        form_data = {'coordenador': self.coordenador.id}
        
        form = DocumentoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('arquivo', form.errors)
    
    def test_coordenador_invalido(self):
        """Testa coordenador com ID inválido"""
        arquivo = SimpleUploadedFile(
            "termo.pdf",
            b"conteudo do pdf",
            content_type="application/pdf"
        )
        
        form_data = {'coordenador': 99999}  # ID inexistente
        form_files = {'arquivo': arquivo}
        
        form = DocumentoForm(data=form_data, files=form_files)
        self.assertFalse(form.is_valid())
        self.assertIn('coordenador', form.errors)
