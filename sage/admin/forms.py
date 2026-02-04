from django import forms
from django.core.validators import MinLengthValidator
import re
from .models import Empresa, Supervisor, Instituicao
from users.models import Usuario


# ==================== FORMULÁRIOS DE INSTITUIÇÃO ====================


class InstituicaoForm(forms.ModelForm):
    """
    Formulário para cadastro de instituição de ensino.
    Campos obrigatórios: Nome, Contato, Endereço completo
    """
    
    class Meta:
        model = Instituicao
        fields = ['nome', 'contato', 'rua', 'numero', 'bairro']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da Instituição'
            }),
            'contato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999 ou email@instituicao.edu.br'
            }),
            'rua': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da rua'
            }),
            'numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro'
            }),
        }
        labels = {
            'nome': 'Nome da Instituição',
            'contato': 'Contato',
            'rua': 'Rua',
            'numero': 'Número',
            'bairro': 'Bairro',
        }
        error_messages = {
            'nome': {
                'required': 'Nome da instituição é obrigatório.',
            },
            'contato': {
                'required': 'Contato é obrigatório.',
            },
            'rua': {
                'required': 'Rua é obrigatória.',
            },
            'numero': {
                'required': 'Número é obrigatório.',
            },
            'bairro': {
                'required': 'Bairro é obrigatório.',
            },
        }
    
    def clean_nome(self):
        """Valida o nome da instituição"""
        nome = self.cleaned_data.get('nome', '')
        
        if not nome or len(nome.strip()) < 3:
            raise forms.ValidationError('Nome da instituição deve ter pelo menos 3 caracteres.')
        
        # Verifica duplicidade (exceto na edição do mesmo registro)
        queryset = Instituicao.objects.filter(nome__iexact=nome.strip())
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Já existe uma instituição cadastrada com este nome.')
        
        return nome.strip()


class InstituicaoEditForm(forms.ModelForm):
    """
    Formulário para edição de instituição.
    """
    
    class Meta:
        model = Instituicao
        fields = ['nome', 'contato', 'rua', 'numero', 'bairro']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da Instituição'
            }),
            'contato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999 ou email@instituicao.edu.br'
            }),
            'rua': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da rua'
            }),
            'numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro'
            }),
        }
        labels = {
            'nome': 'Nome da Instituição',
            'contato': 'Contato',
            'rua': 'Rua',
            'numero': 'Número',
            'bairro': 'Bairro',
        }

# ==================== FORMULÁRIOS DE EMPRESA ====================
# Sprint 03 - TASK 22167 - Criar tela de cadastro de empresa com campos obrigatórios


class EmpresaForm(forms.ModelForm):
    """
    Formulário para cadastro de empresa com campos obrigatórios.
    TASK 22167 - [FRONT] Criar tela de cadastro de empresa com campos obrigatórios
    
    Campos obrigatórios: CNPJ, Razão Social, Endereço completo
    """
    
    class Meta:
        model = Empresa
        fields = ['cnpj', 'razao_social', 'rua', 'numero', 'bairro']
        widgets = {
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00.000.000/0000-00',
                'maxlength': '18'
            }),
            'razao_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razão Social da Empresa'
            }),
            'rua': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da rua'
            }),
            'numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro'
            }),
        }
        labels = {
            'cnpj': 'CNPJ',
            'razao_social': 'Razão Social',
            'rua': 'Rua',
            'numero': 'Número',
            'bairro': 'Bairro',
        }
        error_messages = {
            'cnpj': {
                'required': 'CNPJ é obrigatório.',
            },
            'razao_social': {
                'required': 'Razão Social é obrigatória.',
            },
            'rua': {
                'required': 'Rua é obrigatória.',
            },
            'numero': {
                'required': 'Número é obrigatório.',
            },
            'bairro': {
                'required': 'Bairro é obrigatório.',
            },
        }
    
    def clean_cnpj(self):
        """Valida o CNPJ (formato e unicidade)"""
        cnpj = self.cleaned_data.get('cnpj', '')
        
        # Remove caracteres não numéricos para validação
        cnpj_numeros = re.sub(r'\D', '', cnpj)
        
        if len(cnpj_numeros) != 14:
            raise forms.ValidationError('CNPJ deve conter 14 dígitos.')
        
        # Verifica duplicidade (exceto na edição do mesmo registro)
        queryset = Empresa.objects.filter(cnpj=cnpj_numeros)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Já existe uma empresa cadastrada com este CNPJ.')
        
        return cnpj_numeros
    
    def clean_razao_social(self):
        """Valida a razão social"""
        razao_social = self.cleaned_data.get('razao_social', '')
        
        if not razao_social or len(razao_social.strip()) < 3:
            raise forms.ValidationError('Razão Social deve ter pelo menos 3 caracteres.')
        
        return razao_social.strip()


class EmpresaEditForm(forms.ModelForm):
    """
    Formulário para edição de empresa (sem alterar CNPJ).
    """
    
    class Meta:
        model = Empresa
        fields = ['razao_social', 'rua', 'numero', 'bairro']
        widgets = {
            'razao_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razão Social da Empresa'
            }),
            'rua': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da rua'
            }),
            'numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro'
            }),
        }
        labels = {
            'razao_social': 'Razão Social',
            'rua': 'Rua',
            'numero': 'Número',
            'bairro': 'Bairro',
        }


# Endpoints da API disponíveis em /api/empresas/


class SupervisorForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de Supervisor.
    CA2 - Supervisor vinculado corretamente a uma empresa
    CA3 - Valida campos obrigatórios: Nome, Cargo, Empresa
    """
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@empresa.com'
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
    
    class Meta:
        model = Supervisor
        fields = ['nome', 'contato', 'cargo', 'empresa']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do Supervisor'
            }),
            'contato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo na empresa'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'nome': 'Nome',
            'contato': 'Contato',
            'cargo': 'Cargo',
            'empresa': 'Empresa',
        }
        error_messages = {
            'nome': {
                'required': 'Nome é obrigatório.',
            },
            'cargo': {
                'required': 'Cargo é obrigatório.',
            },
            'empresa': {
                'required': 'Empresa é obrigatória.',
            },
        }
    
    def __init__(self, *args, **kwargs):
        # Permite passar o flag para edição (sem campos de usuário)
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        
        # Remove campos de usuário na edição
        if self.is_edit:
            del self.fields['email']
            del self.fields['senha']
        
        # Ordena empresas por razão social
        self.fields['empresa'].queryset = Empresa.objects.all().order_by('razao_social')
    
    def clean_email(self):
        """Valida que o email não está duplicado"""
        if self.is_edit:
            return None
        
        email = self.cleaned_data.get('email', '')
        
        if not email:
            raise forms.ValidationError('Email é obrigatório.')
        
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Já existe um usuário cadastrado com este email.')
        
        return email
    
    def save(self, commit=True):
        """Salva o supervisor e cria o usuário associado"""
        supervisor = super().save(commit=False)
        
        # Se for criação (não edição), cria o usuário
        if not self.is_edit and not supervisor.pk:
            email = self.cleaned_data.get('email')
            senha = self.cleaned_data.get('senha')
            
            usuario = Usuario.objects.create_user(
                username=email,
                email=email,
                password=senha,
                tipo='supervisor'
            )
            supervisor.usuario = usuario
        
        if commit:
            supervisor.save()
        
        return supervisor


class SupervisorEditForm(forms.ModelForm):
    """
    Formulário simplificado para edição de Supervisor (sem campos de usuário).
    CA3 - Valida campos obrigatórios: Nome, Cargo, Empresa
    """
    
    class Meta:
        model = Supervisor
        fields = ['nome', 'contato', 'cargo', 'empresa']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do Supervisor'
            }),
            'contato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo na empresa'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'nome': 'Nome',
            'contato': 'Contato',
            'cargo': 'Cargo',
            'empresa': 'Empresa',
        }
        error_messages = {
            'nome': {
                'required': 'Nome é obrigatório.',
            },
            'cargo': {
                'required': 'Cargo é obrigatório.',
            },
            'empresa': {
                'required': 'Empresa é obrigatória.',
            },
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordena empresas por razão social
        self.fields['empresa'].queryset = Empresa.objects.all().order_by('razao_social')
