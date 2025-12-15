# Notificação para registro de alertas enviados
from django.db import models
from django.utils import timezone
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
        ('finalizado', 'Finalizado'),
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

    enviado_por = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='documentos_enviados')
    
    # Campos de auditoria
    aprovado_por = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='documentos_avaliados')
    data_aprovacao = models.DateTimeField(null=True, blank=True)

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


class DocumentoHistorico(models.Model):
    """Modelo para registrar histórico de validações de documentos"""
    ACAO_CHOICES = [
        ('enviado', 'Documento Enviado'),
        ('aprovado', 'Aprovado pelo Supervisor'),
        ('reprovado', 'Reprovado pelo Supervisor'),
        ('ajustes_solicitados', 'Ajustes Solicitados'),
        ('corrigido', 'Documento Corrigido'),
        ('finalizado', 'Aprovado pelo Coordenador'),
    ]
    
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='historico')
    acao = models.CharField(max_length=30, choices=ACAO_CHOICES)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    observacoes = models.TextField(null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Histórico de Documento'
        verbose_name_plural = 'Históricos de Documentos'
    
    def __str__(self):
        return f"{self.get_acao_display()} - {self.documento.nome_arquivo} - {self.data_hora}"

class HorasCumpridas(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='horas')
    data = models.DateField()
    quantidade = models.PositiveIntegerField()
    descricao = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.data} - {self.quantidade}h"
    
class Notificacao(models.Model):
    destinatario = models.CharField(max_length=255)
    assunto = models.CharField(max_length=255)
    mensagem = models.TextField()
    data_envio = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=255, blank=True, null=True)  # Ex: documento_id ou outro identificador

    class Meta:
        unique_together = ('destinatario', 'assunto', 'referencia')  # Impede duplicidade

    def __str__(self):
        return f"Notificação para {self.destinatario} - {self.assunto} ({self.data_envio})"


class FeedbackSupervisor(models.Model):
    """Modelo para armazenar feedbacks do supervisor para o aluno"""
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='feedbacks')
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE, related_name='feedbacks_dados')
    estagio = models.ForeignKey(Estagio, on_delete=models.CASCADE, related_name='feedbacks')
    conteudo = models.TextField()
    data_feedback = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_feedback']
        verbose_name = 'Feedback do Supervisor'
        verbose_name_plural = 'Feedbacks do Supervisor'
    
    def __str__(self):
        return f"Feedback de {self.supervisor.nome} para {self.aluno.nome} - {self.data_feedback.strftime('%d/%m/%Y')}"
