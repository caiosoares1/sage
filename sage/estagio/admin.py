from django.contrib import admin
from .models import Aluno, Estagio, Avaliacao, Documento

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'contato', 'instituicao')
    search_fields = ('nome', 'matricula')
    list_filter = ('instituicao',)

@admin.register(Estagio)
class EstagioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'cargo', 'empresa', 'supervisor', 'data_inicio', 'data_fim', 'status')
    list_filter = ('status', 'empresa')
    search_fields = ('titulo', 'cargo')
    date_hierarchy = 'data_inicio'

@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('estagio', 'supervisor', 'nota', 'data_avaliacao')
    list_filter = ('data_avaliacao',)
    search_fields = ('estagio__titulo',)

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome_arquivo', 'tipo', 'estagio', 'coordenador', 'data_envio', 'versao')
    list_filter = ('tipo', 'data_envio')
    search_fields = ('nome_arquivo', 'estagio__titulo')
