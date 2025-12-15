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


