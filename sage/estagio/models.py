from django.db import models
from admin.models import Instituicao
from users.models import Usuario
from admin.models import Supervisor
from admin.models import Empresa
from admin.models import CursoCoordenador

class Aluno(models.Model):
    """Modelo de aluno especializado de usuário"""
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    contato = models.CharField(max_length=30)
    matricula = models.CharField(max_length=11, unique=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE)
    estagio = models.ForeignKey('Estagio', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.matricula}"



class Estagio(models.Model):
    STATUS_CHOICES = [
        ('analise', 'Em análise'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]

    data_inicio = models.DateField()
    titulo = models.CharField(max_length=30)
    cargo = models.CharField(max_length=50)
    carga_horaria = models.IntegerField()
    data_fim = models.DateField()

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='analise'
    )

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
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('ajustes_solicitados', 'Ajustes solicitados'),
        ('corrigido', 'Corrigido'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
        ('substituido', 'Substituído'),
    ]

    data_envio = models.DateField()
    versao = models.FloatField()
    nome_arquivo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50)

    arquivo = models.FileField(upload_to='documentos/')

    estagio = models.ForeignKey(Estagio, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    coordenador = models.ForeignKey(CursoCoordenador, on_delete=models.CASCADE)

    parent = models.ForeignKey('self', null=True, blank=True, related_name='versions', on_delete=models.SET_NULL)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='enviado')

    observacoes_supervisor = models.TextField(null=True, blank=True)

    prazo_limite = models.DateField(null=True, blank=True)

    enviado_por = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_arquivo

    def get_history(self):
        """
        Retorna lista com a cadeia de versões: a versão atual e todas as versões anteriores.
        A ordem pode ser do mais antigo para o mais recente se desejado.
        """
        history = []
        # navegar para trás até a raiz
        node = self
        while node:
            history.append(node)
            node = node.parent
        # history contém [atual, parent, parent.parent, ...]; inverter para mostrar do mais antigo
        return list(reversed(history))



