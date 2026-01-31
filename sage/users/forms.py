from django import forms
from .models import Usuario, NivelAcesso


# ==================== FORMULÁRIOS DE NÍVEL DE ACESSO ====================

class NivelAcessoForm(forms.ModelForm):
    """
    Formulário para criação de níveis de acesso.
    
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    
    BDD:
    DADO que o administrador gerencia permissões
    QUANDO criar um nível de acesso
    ENTÃO o sistema deve armazenar as configurações corretamente
    """
    
    nome = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome do nível de acesso'
        }),
        label='Nome',
        error_messages={
            'required': 'Nome é obrigatório.',
            'max_length': 'Nome deve ter no máximo 100 caracteres.',
        }
    )
    
    descricao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descrição do nível de acesso',
            'rows': 3
        }),
        label='Descrição'
    )
    
    ativo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Ativo'
    )
    
    class Meta:
        model = NivelAcesso
        fields = ['nome', 'descricao', 'permissoes', 'ativo']
        widgets = {
            'permissoes': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_nome(self):
        """Valida que o nome não está vazio e é único"""
        nome = self.cleaned_data.get('nome', '')
        
        if not nome or not nome.strip():
            raise forms.ValidationError('Nome é obrigatório.')
        
        # Verifica duplicidade (exceto na edição do mesmo registro)
        queryset = NivelAcesso.objects.filter(nome__iexact=nome.strip())
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Já existe um nível de acesso com este nome.')
        
        return nome.strip()
    
    def save(self, commit=True):
        """
        Salva o nível de acesso.
        CA1 - Permite a criação de níveis de acesso
        """
        nivel = super().save(commit=commit)
        return nivel


class NivelAcessoEditForm(forms.ModelForm):
    """
    Formulário para edição de níveis de acesso.
    
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    
    BDD:
    DADO que o administrador gerencia permissões
    QUANDO alterar níveis de acesso
    ENTÃO o sistema deve aplicar as permissões corretamente
    """
    
    nome = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome do nível de acesso'
        }),
        label='Nome',
        error_messages={
            'required': 'Nome é obrigatório.',
            'max_length': 'Nome deve ter no máximo 100 caracteres.',
        }
    )
    
    descricao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descrição do nível de acesso',
            'rows': 3
        }),
        label='Descrição'
    )
    
    ativo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Ativo'
    )
    
    class Meta:
        model = NivelAcesso
        fields = ['nome', 'descricao', 'permissoes', 'ativo']
        widgets = {
            'permissoes': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_nome(self):
        """Valida que o nome não está vazio e é único"""
        nome = self.cleaned_data.get('nome', '')
        
        if not nome or not nome.strip():
            raise forms.ValidationError('Nome é obrigatório.')
        
        # Verifica duplicidade (exceto na edição do mesmo registro)
        queryset = NivelAcesso.objects.filter(nome__iexact=nome.strip())
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Já existe um nível de acesso com este nome.')
        
        return nome.strip()
    
    def save(self, commit=True):
        """
        Salva o nível de acesso e aplica permissões imediatamente.
        CA1 - Permite a edição de níveis de acesso
        CA2 - Aplica as permissões imediatamente aos usuários
        """
        nivel = super().save(commit=commit)
        
        # CA2 - As permissões são aplicadas automaticamente via signal
        # quando o m2m de permissoes é alterado
        
        return nivel


# ==================== FORMULÁRIOS DE USUÁRIO ====================


class UsuarioForm(forms.ModelForm):
    """
    Formulário para cadastro de usuários do sistema.
    CA1 - Valida campos obrigatórios: nome (first_name), email
    CA2 - Permite a definição de perfil de acesso no cadastro (tipo)
    """
    
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome completo do usuário'
        }),
        label='Nome',
        error_messages={
            'required': 'Nome é obrigatório.',
            'max_length': 'Nome deve ter no máximo 150 caracteres.',
        }
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemplo.com'
        }),
        label='Email',
        error_messages={
            'required': 'Email é obrigatório.',
            'invalid': 'Informe um email válido.',
        }
    )
    
    senha = forms.CharField(
        required=True,
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 6 caracteres'
        }),
        label='Senha',
        error_messages={
            'required': 'Senha é obrigatória.',
            'min_length': 'Senha deve ter pelo menos 6 caracteres.',
        }
    )
    
    confirmar_senha = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme a senha'
        }),
        label='Confirmar Senha',
        error_messages={
            'required': 'Confirmação de senha é obrigatória.',
        }
    )
    
    tipo = forms.ChoiceField(
        choices=Usuario.USER_TYPES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Perfil de Acesso',
        error_messages={
            'required': 'Perfil de acesso é obrigatório.',
            'invalid_choice': 'Selecione um perfil de acesso válido.',
        }
    )
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'email', 'tipo']
    
    def clean_email(self):
        """Valida que o email não está duplicado"""
        email = self.cleaned_data.get('email', '')
        
        if not email:
            raise forms.ValidationError('Email é obrigatório.')
        
        # Verifica duplicidade (exceto na edição do mesmo registro)
        queryset = Usuario.objects.filter(email=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Já existe um usuário cadastrado com este email.')
        
        return email
    
    def clean_first_name(self):
        """Valida que o nome não está vazio"""
        first_name = self.cleaned_data.get('first_name', '')
        
        if not first_name or not first_name.strip():
            raise forms.ValidationError('Nome é obrigatório.')
        
        return first_name.strip()
    
    def clean(self):
        """Valida que as senhas conferem"""
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        
        if senha and confirmar_senha and senha != confirmar_senha:
            raise forms.ValidationError('As senhas não conferem.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Salva o usuário com a senha criptografada"""
        usuario = super().save(commit=False)
        
        # Define o username como o email
        usuario.username = self.cleaned_data['email']
        
        # Define a senha criptografada
        usuario.set_password(self.cleaned_data['senha'])
        
        if commit:
            usuario.save()
        
        return usuario


class UsuarioEditForm(forms.ModelForm):
    """
    Formulário para edição de usuários do sistema (sem alteração de senha).
    
    US: Edição de usuários existentes
    CA3 - O sistema deve permitir a edição de dados básicos do usuário
    CA4 - O sistema deve permitir a manutenção da integridade do perfil de acesso
    
    BDD:
    DADO que um usuário já está cadastrado
    QUANDO o administrador editar seus dados
    ENTÃO as informações devem ser atualizadas corretamente
    """
    
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome completo do usuário'
        }),
        label='Nome',
        error_messages={
            'required': 'Nome é obrigatório.',
            'max_length': 'Nome deve ter no máximo 150 caracteres.',
        }
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemplo.com'
        }),
        label='Email',
        error_messages={
            'required': 'Email é obrigatório.',
            'invalid': 'Informe um email válido.',
        }
    )
    
    tipo = forms.ChoiceField(
        choices=Usuario.USER_TYPES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Perfil de Acesso',
        error_messages={
            'required': 'Perfil de acesso é obrigatório.',
            'invalid_choice': 'Selecione um perfil de acesso válido.',
        }
    )
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'email', 'tipo']
    
    def clean_email(self):
        """Valida que o email não está duplicado"""
        email = self.cleaned_data.get('email', '')
        
        if not email:
            raise forms.ValidationError('Email é obrigatório.')
        
        # Verifica duplicidade (exceto na edição do mesmo registro)
        queryset = Usuario.objects.filter(email=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Já existe um usuário cadastrado com este email.')
        
        return email
    
    def clean_first_name(self):
        """Valida que o nome não está vazio"""
        first_name = self.cleaned_data.get('first_name', '')
        
        if not first_name or not first_name.strip():
            raise forms.ValidationError('Nome é obrigatório.')
        
        return first_name.strip()
    
    def clean_tipo(self):
        """
        CA4 - Valida a integridade do perfil de acesso.
        Garante que o tipo seja um valor válido dentre as opções permitidas.
        """
        tipo = self.cleaned_data.get('tipo', '')
        
        if not tipo:
            raise forms.ValidationError('Perfil de acesso é obrigatório.')
        
        tipos_validos = [choice[0] for choice in Usuario.USER_TYPES]
        if tipo not in tipos_validos:
            raise forms.ValidationError('Perfil de acesso inválido.')
        
        return tipo
    
    def save(self, commit=True):
        """
        Salva o usuário atualizando os dados básicos.
        CA3 - Atualiza dados básicos (nome, email)
        CA4 - Mantém a integridade do perfil de acesso
        """
        usuario = super().save(commit=False)
        
        # Atualiza o username para o email
        usuario.username = self.cleaned_data['email']
        
        if commit:
            usuario.save()
        
        return usuario
