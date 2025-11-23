from django.contrib import admin
from .models import Instituicao, Empresa, Supervisor, CursoCoordenador

@admin.register(Instituicao)
class InstituicaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'contato', 'rua', 'numero', 'bairro')
    search_fields = ('nome', 'contato')

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'cnpj', 'rua', 'numero', 'bairro')
    search_fields = ('razao_social', 'cnpj')

@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cargo', 'contato', 'empresa')
    list_filter = ('empresa',)
    search_fields = ('nome', 'cargo')

@admin.register(CursoCoordenador)
class CursoCoordenadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'nome_curso', 'codigo_curso', 'contato', 'instituicao')
    list_filter = ('instituicao',)
    search_fields = ('nome', 'nome_curso')
