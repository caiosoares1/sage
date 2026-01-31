from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Usuario, NivelAcesso
from .forms import UsuarioForm, UsuarioEditForm, NivelAcessoForm, NivelAcessoEditForm


# ==================== VIEWS DE NÍVEL DE ACESSO ====================

@login_required
def listar_niveis_acesso(request):
    """
    View para listar todos os níveis de acesso cadastrados.
    
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    """
    niveis = NivelAcesso.objects.all().order_by('nome')
    
    # Filtro por nome
    filtro_nome = request.GET.get('nome', '')
    if filtro_nome:
        niveis = niveis.filter(nome__icontains=filtro_nome)
    
    # Filtro por status ativo
    filtro_ativo = request.GET.get('ativo', '')
    if filtro_ativo:
        niveis = niveis.filter(ativo=(filtro_ativo == 'true'))
    
    context = {
        'niveis': niveis,
        'filtro_nome': filtro_nome,
        'filtro_ativo': filtro_ativo,
    }
    return render(request, 'users/listar_niveis_acesso.html', context)


@login_required
def visualizar_nivel_acesso(request, nivel_id):
    """View para visualizar detalhes de um nível de acesso"""
    nivel = get_object_or_404(NivelAcesso, id=nivel_id)
    
    context = {
        'nivel': nivel,
        'usuarios_associados': nivel.usuarios.all(),
        'permissoes': nivel.permissoes.all(),
    }
    return render(request, 'users/visualizar_nivel_acesso.html', context)


@login_required
def criar_nivel_acesso(request):
    """
    View para criar um novo nível de acesso.
    
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    
    BDD:
    DADO que o administrador gerencia permissões
    QUANDO criar um nível de acesso
    ENTÃO o sistema deve armazenar as configurações corretamente
    """
    if request.method == 'POST':
        form = NivelAcessoForm(request.POST)
        if form.is_valid():
            nivel = form.save()
            messages.success(
                request, 
                f"Nível de acesso '{nivel.nome}' criado com sucesso!"
            )
            return redirect('users:visualizar_nivel_acesso', nivel_id=nivel.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = NivelAcessoForm()
    
    context = {
        'form': form,
    }
    return render(request, 'users/criar_nivel_acesso.html', context)


@login_required
def editar_nivel_acesso(request, nivel_id):
    """
    View para editar um nível de acesso existente.
    
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    
    BDD:
    DADO que o administrador gerencia permissões
    QUANDO alterar níveis de acesso
    ENTÃO o sistema deve aplicar as permissões corretamente
    """
    nivel = get_object_or_404(NivelAcesso, id=nivel_id)
    
    # Armazena permissões originais para comparação
    permissoes_originais = set(nivel.permissoes.values_list('id', flat=True))
    
    if request.method == 'POST':
        form = NivelAcessoEditForm(request.POST, instance=nivel)
        if form.is_valid():
            nivel = form.save()
            
            # Verifica se houve alteração nas permissões
            permissoes_novas = set(nivel.permissoes.values_list('id', flat=True))
            permissoes_alteradas = permissoes_originais != permissoes_novas
            
            # CA2 - Conta quantos usuários foram afetados
            usuarios_afetados = nivel.usuarios.count()
            
            if permissoes_alteradas and usuarios_afetados > 0:
                messages.success(
                    request, 
                    f"Nível de acesso '{nivel.nome}' atualizado com sucesso! "
                    f"Permissões aplicadas imediatamente a {usuarios_afetados} usuário(s)."
                )
            else:
                messages.success(
                    request, 
                    f"Nível de acesso '{nivel.nome}' atualizado com sucesso!"
                )
            return redirect('users:visualizar_nivel_acesso', nivel_id=nivel.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = NivelAcessoEditForm(instance=nivel)
    
    context = {
        'form': form,
        'nivel': nivel,
        'permissoes_originais': permissoes_originais,
    }
    return render(request, 'users/editar_nivel_acesso.html', context)


@login_required
def aplicar_permissoes_nivel(request, nivel_id):
    """
    View para forçar a aplicação imediata das permissões de um nível a todos os usuários.
    
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    """
    nivel = get_object_or_404(NivelAcesso, id=nivel_id)
    
    if request.method == 'POST':
        usuarios_afetados = nivel.aplicar_permissoes_usuarios()
        
        messages.success(
            request, 
            f"Permissões do nível '{nivel.nome}' aplicadas com sucesso a {usuarios_afetados} usuário(s)!"
        )
        return redirect('users:visualizar_nivel_acesso', nivel_id=nivel.id)
    
    return redirect('users:visualizar_nivel_acesso', nivel_id=nivel.id)


@login_required
def atribuir_nivel_acesso(request, usuario_id):
    """
    View para atribuir um nível de acesso a um usuário.
    
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    """
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        nivel_id = request.POST.get('nivel_acesso')
        
        if nivel_id:
            nivel = get_object_or_404(NivelAcesso, id=nivel_id)
            usuario.nivel_acesso = nivel
            usuario.save()
            
            # CA2 - Permissões são aplicadas automaticamente via signal
            
            messages.success(
                request, 
                f"Nível de acesso '{nivel.nome}' atribuído a '{usuario.first_name}' com sucesso! "
                f"Permissões aplicadas imediatamente."
            )
        else:
            # Remove o nível de acesso
            usuario.nivel_acesso = None
            usuario.user_permissions.clear()
            usuario.save()
            
            messages.success(
                request, 
                f"Nível de acesso removido de '{usuario.first_name}'."
            )
        
        return redirect('users:visualizar_usuario', usuario_id=usuario.id)
    
    context = {
        'usuario': usuario,
        'niveis': NivelAcesso.objects.filter(ativo=True).order_by('nome'),
    }
    return render(request, 'users/atribuir_nivel_acesso.html', context)


# ==================== VIEWS DE USUÁRIO ====================

@login_required
def listar_usuarios(request):
    """
    View para listar todos os usuários cadastrados no sistema.
    Permite filtrar por nome, email e tipo de usuário.
    """
    usuarios = Usuario.objects.all().order_by('first_name', 'email')
    
    # Filtro por nome
    filtro_nome = request.GET.get('nome', '')
    if filtro_nome:
        usuarios = usuarios.filter(first_name__icontains=filtro_nome)
    
    # Filtro por email
    filtro_email = request.GET.get('email', '')
    if filtro_email:
        usuarios = usuarios.filter(email__icontains=filtro_email)
    
    # Filtro por tipo de perfil
    filtro_tipo = request.GET.get('tipo', '')
    if filtro_tipo:
        usuarios = usuarios.filter(tipo=filtro_tipo)
    
    context = {
        'usuarios': usuarios,
        'filtro_nome': filtro_nome,
        'filtro_email': filtro_email,
        'filtro_tipo': filtro_tipo,
        'tipos_usuario': Usuario.USER_TYPES,
    }
    return render(request, 'users/listar_usuarios.html', context)


@login_required
def visualizar_usuario(request, usuario_id):
    """View para visualizar detalhes de um usuário"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    context = {
        'usuario': usuario,
    }
    return render(request, 'users/visualizar_usuario.html', context)


@login_required
def cadastrar_usuario(request):
    """
    View para cadastrar um novo usuário no sistema.
    CA1 - O sistema deve permitir o cadastro de usuário com dados obrigatórios (nome, email)
    CA2 - O sistema deve permitir a definição de perfil de acesso no cadastro
    
    BDD:
    DADO que o administrador acessa o sistema
    QUANDO cadastrar um novo usuário
    ENTÃO o usuário deve ser criado com perfil definido
    """
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request, 
                f"Usuário '{usuario.first_name}' cadastrado com sucesso com perfil '{usuario.get_tipo_display()}'!"
            )
            return redirect('users:visualizar_usuario', usuario_id=usuario.id)
        else:
            # Adiciona erros do formulário como mensagens
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = UsuarioForm()
    
    context = {
        'form': form,
    }
    return render(request, 'users/cadastrar_usuario.html', context)


@login_required
def editar_usuario(request, usuario_id):
    """
    View para editar um usuário existente.
    
    US: Edição de usuários existentes
    CA3 - O sistema deve permitir a edição de dados básicos do usuário
    CA4 - O sistema deve permitir a manutenção da integridade do perfil de acesso
    
    BDD:
    DADO que um usuário já está cadastrado
    QUANDO o administrador editar seus dados
    ENTÃO as informações devem ser atualizadas corretamente
    """
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Armazena o perfil original para verificação de integridade (CA4)
    perfil_original = usuario.tipo
    
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save()
            
            # CA4 - Verifica se houve alteração no perfil de acesso
            perfil_alterado = perfil_original != usuario.tipo
            
            if perfil_alterado:
                messages.success(
                    request, 
                    f"Usuário '{usuario.first_name}' atualizado com sucesso! "
                    f"Perfil alterado de '{dict(Usuario.USER_TYPES).get(perfil_original)}' "
                    f"para '{usuario.get_tipo_display()}'."
                )
            else:
                messages.success(
                    request, 
                    f"Usuário '{usuario.first_name}' atualizado com sucesso!"
                )
            return redirect('users:visualizar_usuario', usuario_id=usuario.id)
        else:
            # Adiciona erros do formulário como mensagens
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = UsuarioEditForm(instance=usuario)
    
    context = {
        'form': form,
        'usuario': usuario,
        'perfil_original': perfil_original,
    }
    return render(request, 'users/editar_usuario.html', context)
