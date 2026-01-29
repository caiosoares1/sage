from django import forms
from django.core.validators import MinLengthValidator
import re
from .models import Empresa, Supervisor
from users.models import Usuario

# ==================== FORMULÁRIOS DE EMPRESA ====================
# Os formulários de Empresa foram migrados para a API REST.
# Use os serializers em admin/serializers.py para validações.
# Endpoints disponíveis em /api/empresas/


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
