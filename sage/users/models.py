from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    # campo para definir o tipo do usuário
    USER_TYPES = (
        ('aluno', 'Aluno'),
        ('supervisor', 'Supervisor'),
        ('coordenador', 'Curso Coordenador'),
    )
    tipo = models.CharField(max_length=20, choices=USER_TYPES)


class Notificacao(models.Model):
    mensagem = models.CharField(max_length=300)
    data_envio = models.DateField()
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return self.mensagem[:30]