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
        ('em_andamento', 'Em andamento'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]
    
    STATUS_VAGA_CHOICES = [
        ('disponivel', 'Vaga Disponível'),
        ('ocupada', 'Vaga Ocupada'),
        ('encerrada', 'Vaga Encerrada'),
    ]

    data_inicio = models.DateField()
    titulo = models.CharField(max_length=30)
    cargo = models.CharField(max_length=50)
    carga_horaria = models.IntegerField()
    data_fim = models.DateField()
    descricao = models.TextField(null=True, blank=True)
    
    # Campo para histórico - aluno que solicitou o estágio
    aluno_solicitante = models.ForeignKey('Aluno', on_delete=models.CASCADE, null=True, blank=True, related_name='estagios_solicitados')
    data_solicitacao = models.DateTimeField(auto_now_add=True, null=True)

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='analise'
    )
    
    # Status da vaga para controle de vinculação - CA7
    status_vaga = models.CharField(
        max_length=20,
        choices=STATUS_VAGA_CHOICES,
        default='disponivel'
    )

    def __str__(self):
        return self.titulo
    
    def is_disponivel(self):
        """Verifica se a vaga está disponível para vínculo - CA4"""
        return self.status_vaga == 'disponivel' and self.status == 'aprovado'
    
    def vincular_aluno(self, aluno, realizado_por=None):
        """
        Vincula um aluno à vaga e atualiza o status - CA7
        Registra o histórico do vínculo - CA8
        """
        from estagio.models import VinculoHistorico
        
        # Atualiza o status da vaga
        self.status_vaga = 'ocupada'
        self.save()
        
        # Vincula o aluno ao estágio
        aluno.estagio = self
        aluno.save()
        
        # Registra no histórico - CA8
        VinculoHistorico.objects.create(
            aluno=aluno,
            estagio=self,
            acao='vinculado',
            realizado_por=realizado_por,
            observacoes=f'Aluno {aluno.nome} vinculado à vaga {self.titulo}'
        )
    
    def desvincular_aluno(self, aluno, realizado_por=None, observacoes=None):
        """
        Desvincula um aluno da vaga
        Registra o histórico do desvinculo - CA8
        """
        from estagio.models import VinculoHistorico
        
        # Registra no histórico antes de desvincular - CA8
        VinculoHistorico.objects.create(
            aluno=aluno,
            estagio=self,
            acao='desvinculado',
            realizado_por=realizado_por,
            observacoes=observacoes or f'Aluno {aluno.nome} desvinculado da vaga {self.titulo}'
        )
        
        # Atualiza o status da vaga para disponível
        self.status_vaga = 'disponivel'
        self.save()
        
        # Remove o vínculo do aluno
        aluno.estagio = None
        aluno.save()
    


class Avaliacao(models.Model):
    """
    Modelo de Avaliação de Desempenho do Estagiário.
    CA1 - Permite avaliação com critérios previamente definidos
    CA2 - Salvamento associado ao período correto
    CA4 - Geração automática da nota final
    CA5 - Parecer textual obrigatório
    CA6 - Disponibilização do parecer para consulta
    """
    PERIODO_CHOICES = [
        ('mensal', 'Mensal'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('final', 'Avaliação Final'),
    ]
    
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('completa', 'Completa'),
        ('enviada', 'Enviada'),
        ('parecer_emitido', 'Parecer Emitido'),
    ]
    
    parecer = models.TextField(max_length=1000, blank=True, null=True)
    nota = models.FloatField(null=True, blank=True)
    data_avaliacao = models.DateField()
    
    # CA2 - Período da avaliação
    periodo = models.CharField(
        max_length=20,
        choices=PERIODO_CHOICES,
        default='mensal'
    )
    periodo_inicio = models.DateField(help_text='Data de início do período avaliado')
    periodo_fim = models.DateField(help_text='Data de fim do período avaliado')
    
    # Status da avaliação
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='rascunho'
    )
    
    # CA4, CA5, CA6 - Parecer e nota final
    parecer_final = models.TextField(
        blank=True,
        null=True,
        help_text='Parecer final obrigatório emitido pelo supervisor - CA5'
    )
    nota_final = models.FloatField(
        null=True,
        blank=True,
        help_text='Nota final calculada automaticamente - CA4'
    )
    data_emissao_parecer = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data e hora da emissão do parecer final'
    )
    parecer_disponivel_consulta = models.BooleanField(
        default=False,
        help_text='Indica se o parecer está disponível para consulta pelo aluno - CA6'
    )

    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    estagio = models.ForeignKey(Estagio, on_delete=models.CASCADE, related_name='avaliacoes')
    aluno = models.ForeignKey('Aluno', on_delete=models.CASCADE, related_name='avaliacoes', null=True, blank=True)
    
    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_avaliacao']
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        # Impede avaliação duplicada para mesmo aluno/período
        unique_together = ['estagio', 'aluno', 'periodo_inicio', 'periodo_fim']

    def __str__(self):
        aluno_nome = self.aluno.nome if self.aluno else 'Sem aluno'
        return f"Avaliação {self.id} - {aluno_nome} ({self.get_periodo_display()})"
    
    def calcular_nota_media(self):
        """Calcula a nota média baseada nas notas dos critérios"""
        notas_criterios = self.notas_criterios.all()
        if not notas_criterios.exists():
            return None
        
        total_peso = sum(nc.criterio.peso for nc in notas_criterios)
        if total_peso == 0:
            return None
        
        soma_ponderada = sum(nc.nota * nc.criterio.peso for nc in notas_criterios)
        return round(soma_ponderada / total_peso, 2)
    
    def is_completa(self):
        """
        Verifica se a avaliação está completa - CA3
        Todos os critérios obrigatórios devem ter nota
        """
        from estagio.models import CriterioAvaliacao, NotaCriterio
        
        criterios_obrigatorios = CriterioAvaliacao.objects.filter(
            ativo=True,
            obrigatorio=True
        )
        
        notas_preenchidas = NotaCriterio.objects.filter(
            avaliacao=self,
            nota__isnull=False
        ).values_list('criterio_id', flat=True)
        
        for criterio in criterios_obrigatorios:
            if criterio.id not in notas_preenchidas:
                return False
        
        return True
    
    def get_criterios_faltantes(self):
        """Retorna lista de critérios obrigatórios ainda não preenchidos"""
        from estagio.models import CriterioAvaliacao, NotaCriterio
        
        criterios_obrigatorios = CriterioAvaliacao.objects.filter(
            ativo=True,
            obrigatorio=True
        )
        
        notas_preenchidas = NotaCriterio.objects.filter(
            avaliacao=self,
            nota__isnull=False
        ).values_list('criterio_id', flat=True)
        
        return criterios_obrigatorios.exclude(id__in=notas_preenchidas)
    
    def enviar(self):
        """
        Envia a avaliação se estiver completa - CA3
        Calcula a nota média e atualiza o status
        """
        if not self.is_completa():
            raise ValueError("Avaliação incompleta. Preencha todos os critérios obrigatórios.")
        
        self.nota = self.calcular_nota_media()
        self.status = 'enviada'
        self.save()
        
        return True
    
    def calcular_nota_final(self):
        """
        CA4 - Calcula automaticamente a nota final
        Baseada na média ponderada dos critérios de avaliação
        """
        nota_calculada = self.calcular_nota_media()
        if nota_calculada is None:
            raise ValueError("Não há notas suficientes para calcular a nota final.")
        return nota_calculada
    
    def validar_parecer_final(self, parecer_texto):
        """
        CA5 - Valida que o parecer textual é obrigatório
        Retorna True se válido, levanta exceção se inválido
        """
        if not parecer_texto or not parecer_texto.strip():
            raise ValueError("O parecer final é obrigatório. Forneça um texto descritivo.")
        
        if len(parecer_texto.strip()) < 50:
            raise ValueError("O parecer final deve ter pelo menos 50 caracteres.")
        
        return True
    
    def emitir_parecer_final(self, parecer_texto, disponibilizar_consulta=True):
        """
        Emite o parecer final com cálculo automático da nota.
        CA4 - Gera nota automática
        CA5 - Parecer textual obrigatório
        CA6 - Disponibiliza para consulta
        
        Args:
            parecer_texto: Texto do parecer final (obrigatório)
            disponibilizar_consulta: Se True, disponibiliza para consulta do aluno
        
        Returns:
            tuple: (nota_final, parecer_final)
        
        Raises:
            ValueError: Se avaliação não está completa ou parecer inválido
        """
        from django.utils import timezone
        
        # Verifica se avaliação está completa
        if not self.is_completa():
            raise ValueError("Avaliação incompleta. Preencha todos os critérios obrigatórios.")
        
        # Verifica se já foi enviada
        if self.status not in ['completa', 'enviada']:
            if self.status == 'parecer_emitido':
                raise ValueError("O parecer final já foi emitido para esta avaliação.")
            raise ValueError("A avaliação deve estar completa ou enviada para emitir parecer.")
        
        # CA5 - Valida parecer obrigatório
        self.validar_parecer_final(parecer_texto)
        
        # CA4 - Calcula nota final automaticamente
        self.nota_final = self.calcular_nota_final()
        
        # CA5 - Armazena parecer final
        self.parecer_final = parecer_texto.strip()
        self.data_emissao_parecer = timezone.now()
        
        # CA6 - Disponibiliza para consulta
        self.parecer_disponivel_consulta = disponibilizar_consulta
        
        # Atualiza status
        self.status = 'parecer_emitido'
        self.save()
        
        return (self.nota_final, self.parecer_final)
    
    def get_parecer_para_consulta(self):
        """
        CA6 - Retorna dados do parecer se disponível para consulta
        
        Returns:
            dict: Dados do parecer ou None se não disponível
        """
        if not self.parecer_disponivel_consulta:
            return None
        
        if self.status != 'parecer_emitido':
            return None
        
        return {
            'nota_final': self.nota_final,
            'parecer_final': self.parecer_final,
            'data_emissao': self.data_emissao_parecer,
            'periodo': self.get_periodo_display(),
            'periodo_inicio': self.periodo_inicio,
            'periodo_fim': self.periodo_fim,
            'supervisor': self.supervisor.nome,
            'aluno': self.aluno.nome if self.aluno else None,
        }
    
    def disponibilizar_parecer_consulta(self, disponibilizar=True):
        """
        CA6 - Controla disponibilização do parecer para consulta
        """
        if self.status != 'parecer_emitido':
            raise ValueError("O parecer deve ser emitido antes de ser disponibilizado.")
        
        self.parecer_disponivel_consulta = disponibilizar
        self.save()
        return self.parecer_disponivel_consulta


class CriterioAvaliacao(models.Model):
    """
    Modelo para critérios de avaliação predefinidos - CA1
    """
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    peso = models.FloatField(default=1.0, help_text='Peso do critério no cálculo da nota final')
    nota_minima = models.FloatField(default=0)
    nota_maxima = models.FloatField(default=10)
    obrigatorio = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0, help_text='Ordem de exibição')
    
    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Critério de Avaliação'
        verbose_name_plural = 'Critérios de Avaliação'
    
    def __str__(self):
        obrig = '(Obrigatório)' if self.obrigatorio else '(Opcional)'
        return f"{self.nome} {obrig}"


class NotaCriterio(models.Model):
    """
    Modelo para armazenar a nota de cada critério em uma avaliação - CA1
    """
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name='notas_criterios')
    criterio = models.ForeignKey(CriterioAvaliacao, on_delete=models.CASCADE)
    nota = models.FloatField(null=True, blank=True)
    observacao = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['avaliacao', 'criterio']
        verbose_name = 'Nota de Critério'
        verbose_name_plural = 'Notas de Critérios'
    
    def __str__(self):
        return f"{self.criterio.nome}: {self.nota}"
    
    def clean(self):
        """Valida que a nota está dentro dos limites do critério"""
        from django.core.exceptions import ValidationError
        
        if self.nota is not None:
            if self.nota < self.criterio.nota_minima:
                raise ValidationError(
                    f'A nota deve ser maior ou igual a {self.criterio.nota_minima}'
                )
            if self.nota > self.criterio.nota_maxima:
                raise ValidationError(
                    f'A nota deve ser menor ou igual a {self.criterio.nota_maxima}'
                )



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

    def get_root(self):
        """
        Retorna o documento raiz da cadeia (primeira versão).
        """
        node = self
        while node.parent:
            node = node.parent
        return node

    def get_latest(self):
        """
        Retorna a versão mais recente da cadeia (navega pelos filhos).
        """
        node = self
        while node.versions.exists():
            node = node.versions.order_by('-versao').first()
        return node

    def get_full_history(self):
        """
        Retorna toda a cadeia de versões do documento, do mais antigo ao mais recente.
        Começa do documento raiz e navega até a versão mais recente.
        """
        # Encontrar o documento raiz
        root = self.get_root()
        
        # Navegar de cima para baixo coletando todas as versões
        history = [root]
        node = root
        while node.versions.exists():
            # Pega o filho (versão seguinte)
            child = node.versions.order_by('versao').first()
            if child:
                history.append(child)
                node = child
            else:
                break
        return history

    def is_latest_version(self):
        """
        Verifica se este documento é a versão mais recente da cadeia.
        """
        return not self.versions.exists()


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
        ordering = ['-data_envio']  # Mais recentes primeiro

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


class Atividade(models.Model):
    """Modelo para registro de atividades realizadas pelo aluno"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Confirmação'),
        ('confirmada', 'Confirmada'),
        ('rejeitada', 'Rejeitada'),
    ]
    
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='atividades')
    estagio = models.ForeignKey(Estagio, on_delete=models.CASCADE, related_name='atividades')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data_realizacao = models.DateField()
    horas_dedicadas = models.PositiveIntegerField(help_text='Horas dedicadas à atividade')
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )
    
    # Campos de auditoria
    data_registro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    # Campos de confirmação/rejeição
    confirmado_por = models.ForeignKey(
        Supervisor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='atividades_confirmadas'
    )
    data_confirmacao = models.DateTimeField(null=True, blank=True)
    justificativa_rejeicao = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-data_realizacao', '-data_registro']
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
    
    def __str__(self):
        return f"{self.titulo} - {self.aluno.nome} ({self.get_status_display()})"
    
    def confirmar(self, supervisor):
        """Confirma a atividade realizada pelo aluno"""
        self.status = 'confirmada'
        self.confirmado_por = supervisor
        self.data_confirmacao = timezone.now()
        self.save()
        
        # Registra no histórico
        AtividadeHistorico.objects.create(
            atividade=self,
            acao='confirmada',
            supervisor=supervisor,
            observacoes=None
        )
    
    def rejeitar(self, supervisor, justificativa):
        """Rejeita a atividade com justificativa obrigatória"""
        self.status = 'rejeitada'
        self.confirmado_por = supervisor
        self.data_confirmacao = timezone.now()
        self.justificativa_rejeicao = justificativa
        self.save()
        
        # Registra no histórico
        AtividadeHistorico.objects.create(
            atividade=self,
            acao='rejeitada',
            supervisor=supervisor,
            observacoes=justificativa
        )


class AtividadeHistorico(models.Model):
    """Modelo para manter o histórico de confirmações/rejeições de atividades - CA5"""
    ACAO_CHOICES = [
        ('registrada', 'Atividade Registrada'),
        ('confirmada', 'Atividade Confirmada'),
        ('rejeitada', 'Atividade Rejeitada'),
    ]
    
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='historico')
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    supervisor = models.ForeignKey(
        Supervisor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    observacoes = models.TextField(null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Histórico de Atividade'
        verbose_name_plural = 'Históricos de Atividades'
    
    def __str__(self):
        return f"{self.get_acao_display()} - {self.atividade.titulo} - {self.data_hora}"


class VinculoHistorico(models.Model):
    """Modelo para registrar o histórico de vínculos entre alunos e vagas - CA8"""
    ACAO_CHOICES = [
        ('vinculado', 'Aluno Vinculado'),
        ('desvinculado', 'Aluno Desvinculado'),
        ('transferido', 'Aluno Transferido'),
    ]
    
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='historico_vinculos')
    estagio = models.ForeignKey(Estagio, on_delete=models.CASCADE, related_name='historico_vinculos')
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    realizado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='vinculos_realizados'
    )
    observacoes = models.TextField(null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Histórico de Vínculo'
        verbose_name_plural = 'Históricos de Vínculos'
    
    def __str__(self):
        return f"{self.get_acao_display()} - {self.aluno.nome} - {self.estagio.titulo} - {self.data_hora}"
