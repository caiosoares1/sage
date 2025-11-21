from django import forms
from .models import Estagio, Documento

class EstagioForm(forms.ModelForm):
    class Meta:
        model = Estagio
        fields = [
            'data_inicio', 'titulo', 'cargo', 'carga_horaria',
            'data_fim', 'empresa', 'supervisor'
        ]


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nome_arquivo', 'tipo', 'arquivo', 'versao', 'coordenador']