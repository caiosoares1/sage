from django.db import models
from admin.models import Instituicao
from users.models import Usuario
from admin.models import Supervisor
from admin.models import Empresa
from estagio.models import Estagio

class Aluno(models.Model):
    """Modelo de aluno especializado de usuário"""
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    contato = models.CharField(max_length=30)
    matricula = models.CharField(max_length=11, unique=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE)
    estagio = models.ForeignKey(Estagio, on_delete=models.cascade, null=True, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.matricula}"



class Estagio(models.Model):
    data_inicio = models.DateField()
    titulo = models.CharField(max_length=30)
    cargo = models.CharField(max_length=50)
    carga_horaria = models.IntegerField()
    data_fim = models.DateField()

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)

    def __str__(self):
        return self.titulo
    


class Avaliacao(models.Model):
    parecer = models.CharField(max_length=500)
    nota = models.FloatField()
    data_avaliacao = models.DateField()

    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    estagio = models.ForeignKey(Estagio, on_delete=models.CASCADE)

    def __str__(self):
        return f"Avaliação {self.id}"



class Documento(models.Model):
    data_envio = models.DateField()
    valor = models.FloatField()
    nome_arquivo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50)

    arquivo = models.FileField(upload_to='documentos/')

    estagio = models.ForeignKey(Estagio, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    coordenador = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome_arquivo


