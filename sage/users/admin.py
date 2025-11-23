from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Notificacao

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo', 'is_staff')
    list_filter = ('tipo', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('tipo',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Adicionais', {'fields': ('tipo',)}),
    )

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('mensagem_resumo', 'usuario', 'data_envio')
    list_filter = ('data_envio',)
    search_fields = ('mensagem', 'usuario__username')
    date_hierarchy = 'data_envio'
    
    def mensagem_resumo(self, obj):
        return obj.mensagem[:50] + '...' if len(obj.mensagem) > 50 else obj.mensagem
    mensagem_resumo.short_description = 'Mensagem'
