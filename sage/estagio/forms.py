from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Estagio, Documento
from admin.models import CursoCoordenador

class EstagioForm(forms.ModelForm):
    class Meta:
        model = Estagio
        fields = [
            'titulo', 'cargo', 'empresa', 'supervisor',
            'data_inicio', 'data_fim', 'carga_horaria'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Estágio em Desenvolvimento Web',
                'maxlength': '30'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Desenvolvedor Junior',
                'maxlength': '50'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-control'
            }),
            'supervisor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_fim': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'carga_horaria': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 20',
                'min': '1',
                'max': '40'
            })
        }
        labels = {
            'titulo': 'Título do Estágio',
            'cargo': 'Cargo/Função',
            'empresa': 'Empresa',
            'supervisor': 'Supervisor',
            'data_inicio': 'Data de Início',
            'data_fim': 'Data de Término',
            'carga_horaria': 'Carga Horária (horas/semana)'
        }

    def clean_data_inicio(self):
        data_inicio = self.cleaned_data.get('data_inicio')
        if data_inicio and data_inicio < date.today():
            raise ValidationError('A data de início não pode ser anterior a hoje.')
        return data_inicio

    def clean_data_fim(self):
        data_fim = self.cleaned_data.get('data_fim')
        data_inicio = self.cleaned_data.get('data_inicio')
        
        if data_fim and data_inicio and data_fim <= data_inicio:
            raise ValidationError('A data de término deve ser posterior à data de início.')
        return data_fim

    def clean_carga_horaria(self):
        carga_horaria = self.cleaned_data.get('carga_horaria')
        if carga_horaria and (carga_horaria < 1 or carga_horaria > 40):
            raise ValidationError('A carga horária deve estar entre 1 e 40 horas por semana.')
        return carga_horaria


class DocumentoForm(forms.ModelForm):
    coordenador = forms.ModelChoiceField(
        queryset=CursoCoordenador.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Coordenador do Curso',
        empty_label='Selecione um coordenador'
    )

    class Meta:
        model = Documento
        fields = ['arquivo']
        widgets = {
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx'
            })
        }
        labels = {
            'arquivo': 'Termo de Compromisso (PDF)'
        }

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo:
            # Validar tamanho do arquivo (max 10MB)
            if arquivo.size > 10 * 1024 * 1024:
                raise ValidationError('O arquivo não pode ser maior que 10MB.')
            
            # Validar extensão (PDF ou DOCX)
            if not (arquivo.name.endswith('.pdf') or arquivo.name.endswith('.docx')):
                raise ValidationError('Apenas arquivos PDF ou DOCX são permitidos.')
        
        return arquivo

    def clean_coordenador(self):
        coordenador = self.cleaned_data.get('coordenador')
        if not coordenador:
            raise ValidationError('Selecione um coordenador.')
        return coordenador