from django.db import models
from users.models import Usuario


class Empresa(models.Model):
    id = models.AutoField(primary_key=True)
    cnpj = models.CharField(max_length=14)
    razao_social = models.CharField(max_length=150)
    rua = models.CharField(max_length=50)
    numero = models.IntegerField()
    bairro = models.CharField(max_length=30)

    def __str__(self):
        return self.razao_social
    

class Instituicao(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    contato = models.CharField(max_length=90)
    numero = models.IntegerField()
    bairro = models.CharField(max_length=30)
    rua = models.CharField(max_length=50)

    def __str__(self):
        return self.nome


class CursoCoordenador(models.Model):
    """Modelo de coordenador de curso especializado de usuário"""
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    contato = models.CharField(max_length=30)
    carga_horaria = models.IntegerField()
    nome_curso = models.CharField(max_length=300)
    codigo_curso = models.IntegerField()
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nome} - {self.nome_curso}"


class Supervisor(models.Model):
    """Modelo de supervisor especializado de usuário"""
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    contato = models.CharField(max_length=30)
    cargo = models.CharField(max_length=50)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nome} - {self.cargo}"