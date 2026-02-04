from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Permission


class NivelAcesso(models.Model):
    """
    Modelo para gerenciamento de níveis de acesso.
    
    US: Gerenciamento de níveis de acesso
    CA1 - O sistema deve permitir a criação e edição de níveis de acesso
    CA2 - O sistema deve realizar a aplicação imediata das permissões aos usuários
    
    BDD:
    DADO que o administrador gerencia permissões
    QUANDO alterar níveis de acesso
    ENTÃO o sistema deve aplicar as permissões corretamente
    """
    
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Nível'
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição'
    )
    permissoes = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='niveis_acesso',
        verbose_name='Permissões'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        verbose_name = 'Nível de Acesso'
        verbose_name_plural = 'Níveis de Acesso'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def aplicar_permissoes_usuarios(self):
        """
        CA2 - Aplica imediatamente as permissões do nível a todos os usuários associados.
        """
        usuarios = self.usuarios.all()
        permissoes = self.permissoes.all()
        
        for usuario in usuarios:
            # Remove permissões antigas deste nível
            for perm in Permission.objects.all():
                if perm not in permissoes:
                    usuario.user_permissions.remove(perm)
            
            # Adiciona as novas permissões
            for perm in permissoes:
                usuario.user_permissions.add(perm)
        
        return usuarios.count()
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o save para garantir atualização de permissões.
        """
        super().save(*args, **kwargs)


class Usuario(AbstractUser):
    # campo para definir o tipo do usuário
    USER_TYPES = (
        ('admin', 'Administrador'),
        ('aluno', 'Aluno'),
        ('supervisor', 'Supervisor'),
        ('coordenador', 'Curso Coordenador'),
    )
    tipo = models.CharField(max_length=20, choices=USER_TYPES)
    
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.tipo == 'admin' or self.is_superuser
    
    nivel_acesso = models.ForeignKey(
        NivelAcesso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        verbose_name='Nível de Acesso'
    )
    
    def aplicar_permissoes_nivel(self):
        """
        CA2 - Aplica as permissões do nível de acesso ao usuário.
        """
        if self.nivel_acesso and self.nivel_acesso.ativo:
            # Limpa permissões atuais
            self.user_permissions.clear()
            
            # Aplica permissões do nível
            for perm in self.nivel_acesso.permissoes.all():
                self.user_permissions.add(perm)
            
            return True
        return False


# ==================== SIGNALS PARA APLICAÇÃO IMEDIATA DE PERMISSÕES ====================

@receiver(m2m_changed, sender=NivelAcesso.permissoes.through)
def nivel_acesso_permissoes_changed(sender, instance, action, **kwargs):
    """
    CA2 - Signal para aplicar permissões imediatamente quando o nível de acesso é alterado.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.aplicar_permissoes_usuarios()


@receiver(post_save, sender='users.Usuario')
def usuario_nivel_acesso_changed(sender, instance, created, **kwargs):
    """
    CA2 - Signal para aplicar permissões quando o usuário é salvo com novo nível de acesso.
    """
    if instance.nivel_acesso:
        instance.aplicar_permissoes_nivel()


