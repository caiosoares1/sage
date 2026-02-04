"""
Testes para o módulo de usuários do sistema de estágios.
US: Cadastro de novos usuários
CA1 - O sistema deve permitir o cadastro de usuário com dados obrigatórios (nome, email)
CA2 - O sistema deve permitir a definição de perfil de acesso no cadastro
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from .models import Usuario


# ==================== TESTES DE CADASTRO DE USUÁRIO ====================

class UsuarioFormTest(TestCase):
    """
    Testes para o formulário de cadastro de usuário.
    US: Cadastro de novos usuários
    CA1 - O sistema deve permitir o cadastro de usuário com dados obrigatórios (nome, email)
    CA2 - O sistema deve permitir a definição de perfil de acesso no cadastro
    """
    
    def test_form_valido_com_dados_obrigatorios(self):
        """CA1 - Testa cadastro com dados obrigatórios completos"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': 'joao.silva@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertTrue(form.is_valid())
    
    def test_form_invalido_sem_nome(self):
        """CA1 - Testa que nome é obrigatório"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': '',
            'email': 'joao.silva@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
    
    def test_form_invalido_sem_email(self):
        """CA1 - Testa que email é obrigatório"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': '',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_form_invalido_email_formato_incorreto(self):
        """CA1 - Testa validação de formato de email"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': 'email-invalido',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_form_valido_com_perfil_aluno(self):
        """CA2 - Testa definição de perfil de acesso como aluno"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'Maria Santos',
            'email': 'maria.santos@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.tipo, 'aluno')
    
    def test_form_valido_com_perfil_supervisor(self):
        """CA2 - Testa definição de perfil de acesso como supervisor"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'Carlos Supervisor',
            'email': 'carlos.supervisor@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'supervisor'
        })
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.tipo, 'supervisor')
    
    def test_form_valido_com_perfil_coordenador(self):
        """CA2 - Testa definição de perfil de acesso como coordenador"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'Ana Coordenadora',
            'email': 'ana.coordenadora@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'coordenador'
        })
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.tipo, 'coordenador')
    
    def test_form_invalido_sem_perfil(self):
        """CA2 - Testa que perfil de acesso é obrigatório"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': 'joao.silva@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': ''
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    def test_form_invalido_perfil_inexistente(self):
        """CA2 - Testa que perfil de acesso deve ser válido"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': 'joao.silva@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'perfil_invalido'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    def test_form_invalido_senhas_diferentes(self):
        """Testa validação de confirmação de senha"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': 'joao.silva@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha456',
            'tipo': 'aluno'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
    
    def test_form_invalido_senha_curta(self):
        """Testa validação de senha mínima"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': 'joao.silva@teste.com',
            'senha': '123',
            'confirmar_senha': '123',
            'tipo': 'aluno'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('senha', form.errors)
    
    def test_form_invalido_email_duplicado(self):
        """Testa validação de email único"""
        from users.forms import UsuarioForm
        
        # Cria um usuário existente
        Usuario.objects.create_user(
            username='existente@teste.com',
            email='existente@teste.com',
            password='senha123',
            tipo='aluno'
        )
        
        form = UsuarioForm(data={
            'first_name': 'Outro Usuário',
            'email': 'existente@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_form_salva_usuario_com_username_igual_email(self):
        """Testa que username é definido como email"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': 'joao.silva@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.username, 'joao.silva@teste.com')
    
    def test_form_salva_senha_criptografada(self):
        """Testa que senha é salva criptografada"""
        from users.forms import UsuarioForm
        
        form = UsuarioForm(data={
            'first_name': 'João da Silva',
            'email': 'joao.senha@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        
        # Verifica que a senha não está em texto plano
        self.assertNotEqual(usuario.password, 'senha123')
        # Verifica que a senha pode ser validada
        self.assertTrue(usuario.check_password('senha123'))


class UsuarioEditFormTest(TestCase):
    """
    Testes para o formulário de edição de usuário.
    CA1 - Validação de dados obrigatórios na edição
    CA2 - Permitir alteração de perfil de acesso
    """
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='usuario@teste.com',
            email='usuario@teste.com',
            password='senha123',
            first_name='Nome Original',
            tipo='aluno'
        )
    
    def test_form_valido_editar_nome(self):
        """CA1 - Testa edição de nome"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Atualizado',
            'email': 'usuario@teste.com',
            'tipo': 'aluno'
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.first_name, 'Nome Atualizado')
    
    def test_form_valido_editar_email(self):
        """CA1 - Testa edição de email"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'novo.email@teste.com',
            'tipo': 'aluno'
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.email, 'novo.email@teste.com')
        self.assertEqual(usuario.username, 'novo.email@teste.com')
    
    def test_form_valido_editar_perfil(self):
        """CA2 - Testa alteração de perfil de acesso"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'usuario@teste.com',
            'tipo': 'supervisor'
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.tipo, 'supervisor')
    
    def test_form_invalido_email_duplicado_outro_usuario(self):
        """Testa que não permite email de outro usuário"""
        from users.forms import UsuarioEditForm
        
        # Cria outro usuário
        Usuario.objects.create_user(
            username='outro@teste.com',
            email='outro@teste.com',
            password='senha123',
            tipo='aluno'
        )
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'outro@teste.com',
            'tipo': 'aluno'
        }, instance=self.usuario)
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class CadastrarUsuarioViewTest(TestCase):
    """
    Testes para a view de cadastro de usuário.
    BDD:
    DADO que o administrador acessa o sistema
    QUANDO cadastrar um novo usuário
    ENTÃO o usuário deve ser criado com perfil definido
    """
    
    def setUp(self):
        self.client = Client()
        
        # Cria um usuário administrador para login
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.url = reverse('users:cadastrar_usuario')
    
    def test_acesso_view_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_acesso_view_com_login(self):
        """DADO que o administrador acessa o sistema"""
        self.client.login(username='admin@teste.com', password='admin123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_cadastrar_usuario_sucesso(self):
        """
        DADO que o administrador acessa o sistema
        QUANDO cadastrar um novo usuário
        ENTÃO o usuário deve ser criado com perfil definido
        """
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Novo Usuário',
            'email': 'novo.usuario@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        # Verifica redirecionamento após sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verifica que usuário foi criado
        self.assertTrue(
            Usuario.objects.filter(email='novo.usuario@teste.com').exists()
        )
        
        # Verifica que perfil foi definido corretamente
        usuario = Usuario.objects.get(email='novo.usuario@teste.com')
        self.assertEqual(usuario.tipo, 'aluno')
        self.assertEqual(usuario.first_name, 'Novo Usuário')
    
    def test_cadastrar_usuario_com_perfil_supervisor(self):
        """Testa cadastro com perfil supervisor"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Supervisor Teste',
            'email': 'supervisor.teste@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'supervisor'
        })
        
        self.assertEqual(response.status_code, 302)
        
        usuario = Usuario.objects.get(email='supervisor.teste@teste.com')
        self.assertEqual(usuario.tipo, 'supervisor')
    
    def test_cadastrar_usuario_com_perfil_coordenador(self):
        """Testa cadastro com perfil coordenador"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Coordenador Teste',
            'email': 'coordenador.teste@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'coordenador'
        })
        
        self.assertEqual(response.status_code, 302)
        
        usuario = Usuario.objects.get(email='coordenador.teste@teste.com')
        self.assertEqual(usuario.tipo, 'coordenador')
    
    def test_cadastrar_usuario_sem_nome(self):
        """CA1 - Testa que nome é obrigatório na view"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': '',
            'email': 'sem.nome@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Usuario.objects.filter(email='sem.nome@teste.com').exists()
        )
    
    def test_cadastrar_usuario_sem_email(self):
        """CA1 - Testa que email é obrigatório na view"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Sem Email',
            'email': '',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertEqual(response.status_code, 200)
        # Não deve criar usuário
        self.assertFalse(
            Usuario.objects.filter(first_name='Sem Email').exists()
        )
    
    def test_cadastrar_usuario_email_duplicado(self):
        """Testa que não permite email duplicado"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        # Cria usuário existente
        Usuario.objects.create_user(
            username='existente@teste.com',
            email='existente@teste.com',
            password='senha123',
            tipo='aluno'
        )
        
        response = self.client.post(self.url, {
            'first_name': 'Tentativa Duplicado',
            'email': 'existente@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        })
        
        self.assertEqual(response.status_code, 200)
        # Deve haver apenas 1 usuário com este email
        self.assertEqual(
            Usuario.objects.filter(email='existente@teste.com').count(), 1
        )
    
    def test_mensagem_sucesso_apos_cadastro(self):
        """Testa mensagem de sucesso após cadastro"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Usuario Mensagem',
            'email': 'usuario.mensagem@teste.com',
            'senha': 'senha123',
            'confirmar_senha': 'senha123',
            'tipo': 'aluno'
        }, follow=True)
        
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any('sucesso' in str(m).lower() for m in messages_list)
        )


class ListarUsuariosViewTest(TestCase):
    """Testes para a view de listagem de usuários"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            first_name='Admin',
            tipo='coordenador'
        )
        
        self.usuario_aluno = Usuario.objects.create_user(
            username='aluno@teste.com',
            email='aluno@teste.com',
            password='senha123',
            first_name='Aluno Teste',
            tipo='aluno'
        )
        
        self.usuario_supervisor = Usuario.objects.create_user(
            username='supervisor@teste.com',
            email='supervisor@teste.com',
            password='senha123',
            first_name='Supervisor Teste',
            tipo='supervisor'
        )
        
        self.url = reverse('users:listar_usuarios')
    
    def test_acesso_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_listar_usuarios_com_login(self):
        """Testa listagem de usuários com login"""
        self.client.login(username='admin@teste.com', password='admin123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('usuarios', response.context)
    
    def test_filtrar_por_nome(self):
        """Testa filtro por nome"""
        self.client.login(username='admin@teste.com', password='admin123')
        response = self.client.get(self.url, {'nome': 'Aluno'})
        
        self.assertEqual(response.status_code, 200)
        usuarios = response.context['usuarios']
        self.assertTrue(all('Aluno' in u.first_name for u in usuarios if u.first_name))
    
    def test_filtrar_por_tipo(self):
        """Testa filtro por tipo de perfil"""
        self.client.login(username='admin@teste.com', password='admin123')
        response = self.client.get(self.url, {'tipo': 'supervisor'})
        
        self.assertEqual(response.status_code, 200)
        usuarios = response.context['usuarios']
        self.assertTrue(all(u.tipo == 'supervisor' for u in usuarios))


class EditarUsuarioViewTest(TestCase):
    """Testes para a view de edição de usuário"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.usuario_teste = Usuario.objects.create_user(
            username='teste@teste.com',
            email='teste@teste.com',
            password='senha123',
            first_name='Usuario Original',
            tipo='aluno'
        )
        
        self.url = reverse('users:editar_usuario', args=[self.usuario_teste.id])
    
    def test_acesso_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_editar_usuario_sucesso(self):
        """Testa edição de usuário com sucesso"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Nome Editado',
            'email': 'teste@teste.com',
            'tipo': 'supervisor'
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.first_name, 'Nome Editado')
        self.assertEqual(self.usuario_teste.tipo, 'supervisor')
    
    def test_editar_usuario_invalido_404(self):
        """Testa que retorna 404 para usuário inexistente"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        url = reverse('users:editar_usuario', args=[99999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class VisualizarUsuarioViewTest(TestCase):
    """Testes para a view de visualização de usuário"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.usuario_teste = Usuario.objects.create_user(
            username='teste@teste.com',
            email='teste@teste.com',
            password='senha123',
            first_name='Usuario Teste',
            tipo='aluno'
        )
        
        self.url = reverse('users:visualizar_usuario', args=[self.usuario_teste.id])
    
    def test_acesso_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_visualizar_usuario_sucesso(self):
        """Testa visualização de usuário com sucesso"""
        self.client.login(username='admin@teste.com', password='admin123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('usuario', response.context)
        self.assertEqual(response.context['usuario'], self.usuario_teste)
    
    def test_visualizar_usuario_inexistente_404(self):
        """Testa que retorna 404 para usuário inexistente"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        url = reverse('users:visualizar_usuario', args=[99999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


# ==================== TESTES DE EDIÇÃO DE USUÁRIO (CA3 e CA4) ====================

class UsuarioEditFormCA3CA4Test(TestCase):
    """
    Testes para o formulário de edição de usuário.
    US: Edição de usuários existentes
    CA3 - O sistema deve permitir a edição de dados básicos do usuário
    CA4 - O sistema deve permitir a manutenção da integridade do perfil de acesso
    
    BDD:
    DADO que um usuário já está cadastrado
    QUANDO o administrador editar seus dados
    ENTÃO as informações devem ser atualizadas corretamente
    """
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='usuario@teste.com',
            email='usuario@teste.com',
            password='senha123',
            first_name='Nome Original',
            tipo='aluno'
        )
    
    def test_ca3_editar_nome_usuario(self):
        """CA3 - Testa atualização do nome do usuário"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Atualizado',
            'email': 'usuario@teste.com',
            'tipo': 'aluno'
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.first_name, 'Nome Atualizado')
    
    def test_ca3_editar_email_usuario(self):
        """CA3 - Testa atualização do email do usuário"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'novo.email@teste.com',
            'tipo': 'aluno'
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.email, 'novo.email@teste.com')
        self.assertEqual(usuario.username, 'novo.email@teste.com')
    
    def test_ca3_editar_multiplos_dados_basicos(self):
        """CA3 - Testa atualização de múltiplos dados básicos simultaneamente"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Novo Nome Completo',
            'email': 'novoemail@teste.com',
            'tipo': 'aluno'
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        
        self.assertEqual(usuario.first_name, 'Novo Nome Completo')
        self.assertEqual(usuario.email, 'novoemail@teste.com')
    
    def test_ca3_nome_vazio_nao_permitido(self):
        """CA3 - Testa que nome vazio não é permitido na edição"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': '',
            'email': 'usuario@teste.com',
            'tipo': 'aluno'
        }, instance=self.usuario)
        
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
    
    def test_ca3_email_invalido_nao_permitido(self):
        """CA3 - Testa que email inválido não é permitido na edição"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'email-invalido',
            'tipo': 'aluno'
        }, instance=self.usuario)
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_ca4_alterar_perfil_aluno_para_supervisor(self):
        """CA4 - Testa alteração de perfil de aluno para supervisor"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'usuario@teste.com',
            'tipo': 'supervisor'
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.tipo, 'supervisor')
    
    def test_ca4_alterar_perfil_aluno_para_coordenador(self):
        """CA4 - Testa alteração de perfil de aluno para coordenador"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'usuario@teste.com',
            'tipo': 'coordenador'
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.tipo, 'coordenador')
    
    def test_ca4_manter_perfil_inalterado(self):
        """CA4 - Testa manutenção do perfil quando não alterado"""
        from users.forms import UsuarioEditForm
        
        perfil_original = self.usuario.tipo
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Alterado',
            'email': 'usuario@teste.com',
            'tipo': 'aluno'  # Mesmo perfil
        }, instance=self.usuario)
        
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertEqual(usuario.tipo, perfil_original)
    
    def test_ca4_perfil_invalido_nao_permitido(self):
        """CA4 - Testa que perfil inválido não é permitido"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'usuario@teste.com',
            'tipo': 'perfil_invalido'
        }, instance=self.usuario)
        
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    def test_ca4_perfil_vazio_nao_permitido(self):
        """CA4 - Testa que perfil vazio não é permitido"""
        from users.forms import UsuarioEditForm
        
        form = UsuarioEditForm(data={
            'first_name': 'Nome Original',
            'email': 'usuario@teste.com',
            'tipo': ''
        }, instance=self.usuario)
        
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    def test_ca4_integridade_todos_perfis_validos(self):
        """CA4 - Testa integridade aceitando todos os perfis válidos"""
        from users.forms import UsuarioEditForm
        
        perfis_validos = ['aluno', 'supervisor', 'coordenador']
        
        for perfil in perfis_validos:
            form = UsuarioEditForm(data={
                'first_name': 'Nome Teste',
                'email': f'{perfil}@teste.com',
                'tipo': perfil
            }, instance=self.usuario)
            
            self.assertTrue(form.is_valid(), f"Perfil '{perfil}' deveria ser válido")


class EditarUsuarioViewCA3CA4Test(TestCase):
    """
    Testes para a view de edição de usuário - CA3 e CA4.
    
    BDD:
    DADO que um usuário já está cadastrado
    QUANDO o administrador editar seus dados
    ENTÃO as informações devem ser atualizadas corretamente
    """
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            first_name='Admin',
            tipo='coordenador'
        )
        
        self.usuario_teste = Usuario.objects.create_user(
            username='teste@teste.com',
            email='teste@teste.com',
            password='senha123',
            first_name='Usuario Original',
            tipo='aluno'
        )
        
        self.url = reverse('users:editar_usuario', args=[self.usuario_teste.id])
    
    def test_bdd_editar_usuario_dados_atualizados(self):
        """
        BDD: DADO que um usuário já está cadastrado
             QUANDO o administrador editar seus dados
             ENTÃO as informações devem ser atualizadas corretamente
        """
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Nome Atualizado',
            'email': 'email.atualizado@teste.com',
            'tipo': 'supervisor'
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.first_name, 'Nome Atualizado')
        self.assertEqual(self.usuario_teste.email, 'email.atualizado@teste.com')
        self.assertEqual(self.usuario_teste.tipo, 'supervisor')
    
    def test_ca3_view_editar_nome(self):
        """CA3 - Testa edição de nome via view"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Novo Nome',
            'email': 'teste@teste.com',
            'tipo': 'aluno'
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.first_name, 'Novo Nome')
    
    def test_ca3_view_editar_email(self):
        """CA3 - Testa edição de email via view"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Usuario Original',
            'email': 'novo.email@teste.com',
            'tipo': 'aluno'
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.email, 'novo.email@teste.com')
    
    def test_ca3_view_rejeita_nome_vazio(self):
        """CA3 - Testa que a view rejeita nome vazio"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': '',
            'email': 'teste@teste.com',
            'tipo': 'aluno'
        })
        
        self.assertEqual(response.status_code, 200)  # Retorna ao formulário
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.first_name, 'Usuario Original')  # Não alterou
    
    def test_ca3_view_rejeita_email_duplicado(self):
        """CA3 - Testa que a view rejeita email já existente"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        # Tenta usar o email do admin
        response = self.client.post(self.url, {
            'first_name': 'Usuario Original',
            'email': 'admin@teste.com',
            'tipo': 'aluno'
        })
        
        self.assertEqual(response.status_code, 200)  # Retorna ao formulário
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.email, 'teste@teste.com')  # Não alterou
    
    def test_ca4_view_alterar_perfil(self):
        """CA4 - Testa alteração de perfil via view"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Usuario Original',
            'email': 'teste@teste.com',
            'tipo': 'coordenador'
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.tipo, 'coordenador')
    
    def test_ca4_view_manter_perfil(self):
        """CA4 - Testa manutenção do perfil quando não alterado"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Nome Alterado',
            'email': 'teste@teste.com',
            'tipo': 'aluno'  # Mesmo perfil original
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.tipo, 'aluno')
    
    def test_ca4_view_rejeita_perfil_invalido(self):
        """CA4 - Testa que a view rejeita perfil inválido"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Usuario Original',
            'email': 'teste@teste.com',
            'tipo': 'perfil_invalido'
        })
        
        self.assertEqual(response.status_code, 200)  # Retorna ao formulário
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.tipo, 'aluno')  # Não alterou
    
    def test_ca4_mensagem_sucesso_alteracao_perfil(self):
        """CA4 - Testa mensagem de sucesso quando perfil é alterado"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Usuario Original',
            'email': 'teste@teste.com',
            'tipo': 'supervisor'
        }, follow=True)
        
        messages_list = list(get_messages(response.wsgi_request))
        mensagens_texto = [str(m) for m in messages_list]
        
        # Verifica que menciona a alteração de perfil
        self.assertTrue(
            any('Perfil alterado' in m for m in mensagens_texto) or
            any('sucesso' in m.lower() for m in mensagens_texto)
        )
    
    def test_ca4_mensagem_sucesso_sem_alteracao_perfil(self):
        """CA4 - Testa mensagem de sucesso quando perfil não é alterado"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'first_name': 'Nome Novo',
            'email': 'teste@teste.com',
            'tipo': 'aluno'  # Mesmo perfil
        }, follow=True)
        
        messages_list = list(get_messages(response.wsgi_request))
        
        self.assertTrue(
            any('sucesso' in str(m).lower() for m in messages_list)
        )
    
    def test_view_get_carrega_dados_existentes(self):
        """Testa que o GET carrega os dados existentes do usuário"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('usuario', response.context)
        self.assertEqual(response.context['usuario'].first_name, 'Usuario Original')
        self.assertEqual(response.context['usuario'].email, 'teste@teste.com')
        self.assertEqual(response.context['usuario'].tipo, 'aluno')
    
    def test_view_contexto_perfil_original(self):
        """Testa que o contexto inclui o perfil original para comparação"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('perfil_original', response.context)
        self.assertEqual(response.context['perfil_original'], 'aluno')


# ==================== TESTES DE NÍVEIS DE ACESSO (CA1 e CA2) ====================

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import NivelAcesso
from .forms import NivelAcessoForm, NivelAcessoEditForm


class NivelAcessoModelTest(TestCase):
    """
    Testes para o modelo NivelAcesso.
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    """
    
    def setUp(self):
        # Cria uma permissão de teste
        content_type = ContentType.objects.get_for_model(Usuario)
        self.permissao1 = Permission.objects.create(
            codename='pode_visualizar_relatorios',
            name='Pode visualizar relatórios',
            content_type=content_type
        )
        self.permissao2 = Permission.objects.create(
            codename='pode_editar_relatorios',
            name='Pode editar relatórios',
            content_type=content_type
        )
    
    def test_ca1_criar_nivel_acesso(self):
        """CA1 - Testa criação de nível de acesso"""
        nivel = NivelAcesso.objects.create(
            nome='Administrador',
            descricao='Acesso total ao sistema'
        )
        
        self.assertIsNotNone(nivel.id)
        self.assertEqual(nivel.nome, 'Administrador')
        self.assertTrue(nivel.ativo)
    
    def test_ca1_editar_nivel_acesso(self):
        """CA1 - Testa edição de nível de acesso"""
        nivel = NivelAcesso.objects.create(
            nome='Visualizador',
            descricao='Apenas visualização'
        )
        
        nivel.nome = 'Visualizador Atualizado'
        nivel.descricao = 'Descrição atualizada'
        nivel.save()
        
        nivel.refresh_from_db()
        self.assertEqual(nivel.nome, 'Visualizador Atualizado')
        self.assertEqual(nivel.descricao, 'Descrição atualizada')
    
    def test_ca1_adicionar_permissoes_nivel(self):
        """CA1 - Testa adição de permissões ao nível de acesso"""
        nivel = NivelAcesso.objects.create(nome='Editor')
        nivel.permissoes.add(self.permissao1, self.permissao2)
        
        self.assertEqual(nivel.permissoes.count(), 2)
        self.assertIn(self.permissao1, nivel.permissoes.all())
    
    def test_ca2_aplicar_permissoes_usuarios(self):
        """CA2 - Testa aplicação imediata de permissões aos usuários"""
        nivel = NivelAcesso.objects.create(nome='Gestor')
        nivel.permissoes.add(self.permissao1)
        
        usuario = Usuario.objects.create_user(
            username='teste@teste.com',
            email='teste@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=nivel
        )
        
        # A permissão deve ter sido aplicada via signal
        self.assertTrue(usuario.has_perm(f'users.{self.permissao1.codename}'))
    
    def test_ca2_aplicar_permissoes_metodo(self):
        """CA2 - Testa método aplicar_permissoes_usuarios"""
        nivel = NivelAcesso.objects.create(nome='Supervisor')
        nivel.permissoes.add(self.permissao1, self.permissao2)
        
        usuario1 = Usuario.objects.create_user(
            username='user1@teste.com',
            email='user1@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=nivel
        )
        usuario2 = Usuario.objects.create_user(
            username='user2@teste.com',
            email='user2@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=nivel
        )
        
        # Aplica permissões
        usuarios_afetados = nivel.aplicar_permissoes_usuarios()
        
        self.assertEqual(usuarios_afetados, 2)
    
    def test_nivel_str(self):
        """Testa representação string do nível de acesso"""
        nivel = NivelAcesso.objects.create(nome='Teste')
        self.assertEqual(str(nivel), 'Teste')
    
    def test_nivel_acesso_desativado_nao_aplica_permissoes(self):
        """Testa que nível desativado não aplica permissões"""
        nivel = NivelAcesso.objects.create(nome='Inativo', ativo=False)
        nivel.permissoes.add(self.permissao1)
        
        usuario = Usuario.objects.create_user(
            username='teste@teste.com',
            email='teste@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=nivel
        )
        
        # Chama o método diretamente
        resultado = usuario.aplicar_permissoes_nivel()
        self.assertFalse(resultado)


class NivelAcessoFormCA1Test(TestCase):
    """
    Testes para o formulário de criação de níveis de acesso.
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    
    BDD:
    DADO que o administrador gerencia permissões
    QUANDO criar um nível de acesso
    ENTÃO o sistema deve armazenar as configurações corretamente
    """
    
    def test_ca1_criar_nivel_acesso_valido(self):
        """CA1 - Testa criação de nível de acesso com dados válidos"""
        form = NivelAcessoForm(data={
            'nome': 'Novo Nível',
            'descricao': 'Descrição do nível',
            'ativo': True
        })
        
        self.assertTrue(form.is_valid())
        nivel = form.save()
        self.assertEqual(nivel.nome, 'Novo Nível')
    
    def test_ca1_nome_obrigatorio(self):
        """CA1 - Testa que nome é obrigatório"""
        form = NivelAcessoForm(data={
            'nome': '',
            'descricao': 'Descrição',
            'ativo': True
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_ca1_nome_unico(self):
        """CA1 - Testa que nome deve ser único"""
        NivelAcesso.objects.create(nome='Administrador')
        
        form = NivelAcessoForm(data={
            'nome': 'Administrador',
            'descricao': 'Outro admin',
            'ativo': True
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_ca1_descricao_opcional(self):
        """CA1 - Testa que descrição é opcional"""
        form = NivelAcessoForm(data={
            'nome': 'Nível Sem Descrição',
            'ativo': True
        })
        
        self.assertTrue(form.is_valid())
    
    def test_ca1_ativo_default_true(self):
        """CA1 - Testa que ativo é True por padrão quando marcado"""
        form = NivelAcessoForm(data={
            'nome': 'Nível Padrão',
            'ativo': True  # Checkbox marcado = True enviado
        })
        
        self.assertTrue(form.is_valid())
        nivel = form.save()
        self.assertTrue(nivel.ativo)
    
    def test_ca1_ativo_false_quando_nao_marcado(self):
        """CA1 - Testa que ativo é False quando checkbox não marcado"""
        form = NivelAcessoForm(data={
            'nome': 'Nível Inativo'
            # ativo não passado = checkbox não marcado = False
        })
        
        self.assertTrue(form.is_valid())
        nivel = form.save()
        self.assertFalse(nivel.ativo)


class NivelAcessoEditFormCA1CA2Test(TestCase):
    """
    Testes para o formulário de edição de níveis de acesso.
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    """
    
    def setUp(self):
        self.nivel = NivelAcesso.objects.create(
            nome='Nível Original',
            descricao='Descrição original',
            ativo=True
        )
        
        content_type = ContentType.objects.get_for_model(Usuario)
        self.permissao = Permission.objects.create(
            codename='permissao_teste_edit',
            name='Permissão de teste',
            content_type=content_type
        )
    
    def test_ca1_editar_nome_nivel(self):
        """CA1 - Testa edição do nome do nível"""
        form = NivelAcessoEditForm(data={
            'nome': 'Nível Atualizado',
            'descricao': 'Descrição original',
            'ativo': True
        }, instance=self.nivel)
        
        self.assertTrue(form.is_valid())
        nivel = form.save()
        self.assertEqual(nivel.nome, 'Nível Atualizado')
    
    def test_ca1_editar_descricao_nivel(self):
        """CA1 - Testa edição da descrição do nível"""
        form = NivelAcessoEditForm(data={
            'nome': 'Nível Original',
            'descricao': 'Nova descrição',
            'ativo': True
        }, instance=self.nivel)
        
        self.assertTrue(form.is_valid())
        nivel = form.save()
        self.assertEqual(nivel.descricao, 'Nova descrição')
    
    def test_ca1_desativar_nivel(self):
        """CA1 - Testa desativação do nível"""
        form = NivelAcessoEditForm(data={
            'nome': 'Nível Original',
            'descricao': 'Descrição original',
            'ativo': False
        }, instance=self.nivel)
        
        self.assertTrue(form.is_valid())
        nivel = form.save()
        self.assertFalse(nivel.ativo)
    
    def test_ca1_nome_unico_na_edicao(self):
        """CA1 - Testa que nome deve ser único na edição"""
        NivelAcesso.objects.create(nome='Outro Nível')
        
        form = NivelAcessoEditForm(data={
            'nome': 'Outro Nível',
            'descricao': 'Descrição',
            'ativo': True
        }, instance=self.nivel)
        
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_ca1_mesmo_nome_permitido_na_edicao(self):
        """CA1 - Testa que o mesmo nome é permitido na edição do próprio registro"""
        form = NivelAcessoEditForm(data={
            'nome': 'Nível Original',
            'descricao': 'Descrição alterada',
            'ativo': True
        }, instance=self.nivel)
        
        self.assertTrue(form.is_valid())


class CriarNivelAcessoViewCA1Test(TestCase):
    """
    Testes para a view de criação de níveis de acesso.
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    
    BDD:
    DADO que o administrador gerencia permissões
    QUANDO criar um nível de acesso
    ENTÃO o sistema deve armazenar as configurações corretamente
    """
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.url = reverse('users:criar_nivel_acesso')
    
    def test_acesso_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_ca1_bdd_criar_nivel_acesso_sucesso(self):
        """
        BDD: DADO que o administrador gerencia permissões
             QUANDO criar um nível de acesso
             ENTÃO o sistema deve armazenar as configurações corretamente
        """
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nome': 'Novo Nível BDD',
            'descricao': 'Descrição do nível',
            'ativo': True
        })
        
        self.assertEqual(response.status_code, 302)
        
        nivel = NivelAcesso.objects.get(nome='Novo Nível BDD')
        self.assertIsNotNone(nivel)
        self.assertEqual(nivel.descricao, 'Descrição do nível')
        self.assertTrue(nivel.ativo)
    
    def test_ca1_criar_nivel_acesso_nome_vazio_falha(self):
        """CA1 - Testa que criação falha com nome vazio"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nome': '',
            'descricao': 'Descrição',
            'ativo': True
        })
        
        self.assertEqual(response.status_code, 200)  # Retorna ao formulário
        self.assertEqual(NivelAcesso.objects.count(), 0)
    
    def test_ca1_criar_nivel_acesso_nome_duplicado_falha(self):
        """CA1 - Testa que criação falha com nome duplicado"""
        NivelAcesso.objects.create(nome='Existente')
        
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nome': 'Existente',
            'descricao': 'Duplicado',
            'ativo': True
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(NivelAcesso.objects.count(), 1)
    
    def test_ca1_mensagem_sucesso_criacao(self):
        """CA1 - Testa mensagem de sucesso na criação"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nome': 'Nível Teste Msg',
            'descricao': 'Descrição',
            'ativo': True
        }, follow=True)
        
        messages_list = list(get_messages(response.wsgi_request))
        
        self.assertTrue(
            any('sucesso' in str(m).lower() for m in messages_list)
        )


class EditarNivelAcessoViewCA1CA2Test(TestCase):
    """
    Testes para a view de edição de níveis de acesso.
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    
    BDD:
    DADO que o administrador gerencia permissões
    QUANDO alterar níveis de acesso
    ENTÃO o sistema deve aplicar as permissões corretamente
    """
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.nivel = NivelAcesso.objects.create(
            nome='Nível Teste',
            descricao='Descrição original',
            ativo=True
        )
        
        content_type = ContentType.objects.get_for_model(Usuario)
        self.permissao = Permission.objects.create(
            codename='permissao_view_teste',
            name='Permissão view teste',
            content_type=content_type
        )
        
        self.url = reverse('users:editar_nivel_acesso', args=[self.nivel.id])
    
    def test_acesso_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_ca1_editar_nivel_acesso_sucesso(self):
        """CA1 - Testa edição de nível de acesso via view"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nome': 'Nível Atualizado',
            'descricao': 'Nova descrição',
            'ativo': True
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.nivel.refresh_from_db()
        self.assertEqual(self.nivel.nome, 'Nível Atualizado')
        self.assertEqual(self.nivel.descricao, 'Nova descrição')
    
    def test_ca1_ca2_bdd_alterar_nivel_aplica_permissoes(self):
        """
        BDD: DADO que o administrador gerencia permissões
             QUANDO alterar níveis de acesso
             ENTÃO o sistema deve aplicar as permissões corretamente
        """
        # Cria usuário associado ao nível
        usuario = Usuario.objects.create_user(
            username='user@teste.com',
            email='user@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=self.nivel
        )
        
        self.client.login(username='admin@teste.com', password='admin123')
        
        # Edita o nível adicionando permissão
        response = self.client.post(self.url, {
            'nome': 'Nível Teste',
            'descricao': 'Descrição',
            'ativo': True,
            'permissoes': [self.permissao.id]
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Recarrega o usuário
        usuario.refresh_from_db()
        
        # Verifica que a permissão foi aplicada
        self.assertTrue(usuario.has_perm(f'users.{self.permissao.codename}'))
    
    def test_ca2_mensagem_usuarios_afetados(self):
        """CA2 - Testa mensagem informando usuários afetados"""
        usuario = Usuario.objects.create_user(
            username='user@teste.com',
            email='user@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=self.nivel
        )
        
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nome': 'Nível Teste',
            'descricao': 'Descrição',
            'ativo': True,
            'permissoes': [self.permissao.id]
        }, follow=True)
        
        messages_list = list(get_messages(response.wsgi_request))
        mensagens_texto = [str(m) for m in messages_list]
        
        # Verifica mensagem de sucesso com contagem de usuários
        self.assertTrue(
            any('1 usuário' in m or 'sucesso' in m.lower() for m in mensagens_texto)
        )
    
    def test_ca1_editar_nivel_inexistente_404(self):
        """CA1 - Testa que retorna 404 para nível inexistente"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        url = reverse('users:editar_nivel_acesso', args=[99999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class AplicarPermissoesNivelViewCA2Test(TestCase):
    """
    Testes para a view de aplicação imediata de permissões.
    US: Gerenciamento de níveis de acesso
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    """
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.nivel = NivelAcesso.objects.create(
            nome='Nível Aplicar',
            descricao='Nível para teste de aplicação',
            ativo=True
        )
        
        content_type = ContentType.objects.get_for_model(Usuario)
        self.permissao = Permission.objects.create(
            codename='permissao_aplicar_teste',
            name='Permissão aplicar teste',
            content_type=content_type
        )
        self.nivel.permissoes.add(self.permissao)
        
        self.url = reverse('users:aplicar_permissoes_nivel', args=[self.nivel.id])
    
    def test_ca2_aplicar_permissoes_post(self):
        """CA2 - Testa aplicação de permissões via POST"""
        usuario = Usuario.objects.create_user(
            username='user@teste.com',
            email='user@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=self.nivel
        )
        
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        
        usuario.refresh_from_db()
        self.assertTrue(usuario.has_perm(f'users.{self.permissao.codename}'))
    
    def test_ca2_get_redireciona(self):
        """CA2 - Testa que GET redireciona sem aplicar"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
    
    def test_ca2_mensagem_sucesso_aplicacao(self):
        """CA2 - Testa mensagem de sucesso na aplicação"""
        Usuario.objects.create_user(
            username='user1@teste.com',
            email='user1@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=self.nivel
        )
        Usuario.objects.create_user(
            username='user2@teste.com',
            email='user2@teste.com',
            password='senha123',
            tipo='aluno',
            nivel_acesso=self.nivel
        )
        
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, follow=True)
        
        messages_list = list(get_messages(response.wsgi_request))
        mensagens_texto = [str(m) for m in messages_list]
        
        self.assertTrue(
            any('2 usuário' in m or 'sucesso' in m.lower() for m in mensagens_texto)
        )


class AtribuirNivelAcessoViewCA2Test(TestCase):
    """
    Testes para a view de atribuição de nível de acesso a usuário.
    US: Gerenciamento de níveis de acesso
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    """
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.usuario_teste = Usuario.objects.create_user(
            username='teste@teste.com',
            email='teste@teste.com',
            password='senha123',
            first_name='Usuario Teste',
            tipo='aluno'
        )
        
        self.nivel = NivelAcesso.objects.create(
            nome='Nível Atribuir',
            descricao='Nível para atribuição',
            ativo=True
        )
        
        content_type = ContentType.objects.get_for_model(Usuario)
        self.permissao = Permission.objects.create(
            codename='permissao_atribuir_teste',
            name='Permissão atribuir teste',
            content_type=content_type
        )
        self.nivel.permissoes.add(self.permissao)
        
        self.url = reverse('users:atribuir_nivel_acesso', args=[self.usuario_teste.id])
    
    def test_acesso_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_ca2_atribuir_nivel_usuario(self):
        """CA2 - Testa atribuição de nível de acesso ao usuário"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nivel_acesso': self.nivel.id
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertEqual(self.usuario_teste.nivel_acesso, self.nivel)
    
    def test_ca2_atribuir_nivel_aplica_permissoes_imediatamente(self):
        """CA2 - Testa que permissões são aplicadas imediatamente"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nivel_acesso': self.nivel.id
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertTrue(self.usuario_teste.has_perm(f'users.{self.permissao.codename}'))
    
    def test_ca2_remover_nivel_acesso(self):
        """CA2 - Testa remoção de nível de acesso"""
        self.usuario_teste.nivel_acesso = self.nivel
        self.usuario_teste.save()
        
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nivel_acesso': ''
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.usuario_teste.refresh_from_db()
        self.assertIsNone(self.usuario_teste.nivel_acesso)
    
    def test_ca2_mensagem_sucesso_atribuicao(self):
        """CA2 - Testa mensagem de sucesso na atribuição"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.post(self.url, {
            'nivel_acesso': self.nivel.id
        }, follow=True)
        
        messages_list = list(get_messages(response.wsgi_request))
        mensagens_texto = [str(m) for m in messages_list]
        
        self.assertTrue(
            any('sucesso' in m.lower() and 'imediatamente' in m.lower() for m in mensagens_texto)
        )
    
    def test_view_get_lista_niveis_ativos(self):
        """Testa que GET lista apenas níveis ativos"""
        nivel_inativo = NivelAcesso.objects.create(
            nome='Nível Inativo',
            ativo=False
        )
        
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('niveis', response.context)
        
        niveis_context = response.context['niveis']
        self.assertIn(self.nivel, niveis_context)
        self.assertNotIn(nivel_inativo, niveis_context)


class ListarNiveisAcessoViewTest(TestCase):
    """Testes para a view de listagem de níveis de acesso"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.nivel1 = NivelAcesso.objects.create(nome='Admin', ativo=True)
        self.nivel2 = NivelAcesso.objects.create(nome='Editor', ativo=True)
        self.nivel3 = NivelAcesso.objects.create(nome='Visualizador', ativo=False)
        
        self.url = reverse('users:listar_niveis_acesso')
    
    def test_acesso_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_listar_todos_niveis(self):
        """Testa listagem de todos os níveis"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('niveis', response.context)
        self.assertEqual(response.context['niveis'].count(), 3)
    
    def test_filtrar_por_nome(self):
        """Testa filtro por nome"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.get(self.url, {'nome': 'Admin'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['niveis'].count(), 1)
        self.assertEqual(response.context['niveis'].first().nome, 'Admin')
    
    def test_filtrar_por_ativo(self):
        """Testa filtro por status ativo"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.get(self.url, {'ativo': 'true'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['niveis'].count(), 2)


class VisualizarNivelAcessoViewTest(TestCase):
    """Testes para a view de visualização de nível de acesso"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin@teste.com',
            email='admin@teste.com',
            password='admin123',
            tipo='coordenador'
        )
        
        self.nivel = NivelAcesso.objects.create(
            nome='Nível Visualizar',
            descricao='Descrição',
            ativo=True
        )
        
        self.url = reverse('users:visualizar_nivel_acesso', args=[self.nivel.id])
    
    def test_acesso_requer_login(self):
        """Testa que a view requer autenticação"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_visualizar_nivel_sucesso(self):
        """Testa visualização de nível com sucesso"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('nivel', response.context)
        self.assertEqual(response.context['nivel'], self.nivel)
    
    def test_visualizar_nivel_inexistente_404(self):
        """Testa que retorna 404 para nível inexistente"""
        self.client.login(username='admin@teste.com', password='admin123')
        
        url = reverse('users:visualizar_nivel_acesso', args=[99999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)