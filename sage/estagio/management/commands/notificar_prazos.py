from django.core.management.base import BaseCommand
from estagio.models import Documento, Notificacao
from django.utils import timezone
from utils.email import enviar_notificacao_email
from estagio.models import Aluno
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envia notificações automáticas para prazos próximos de documentos.'

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=3, help='Dias de antecedência para alertar')

    def handle(self, *args, **options):
        hoje = timezone.now().date()
        dias_alerta = options['dias']  # CA2 - Período mínimo configurável
        # CA1 - Identifica documentos com prazos próximos automaticamente
        # CA4 - Não envia para documentos já entregues (status aprovado, finalizado, substituido)
        documentos = Documento.objects.filter(
            prazo_limite__isnull=False
        ).exclude(
            status__in=['aprovado', 'finalizado', 'substituido', 'enviado', 'corrigido']
        )
        
        notificacoes_enviadas = 0
        
        for doc in documentos:
            if doc.prazo_limite:
                dias_restantes = (doc.prazo_limite - hoje).days
                if 0 <= dias_restantes <= dias_alerta:
                    try:
                        aluno = Aluno.objects.get(estagio=doc.estagio)
                        destinatario = aluno.contato
                        # CA3 - Notificação informa nome do documento e data limite
                        assunto = f"Alerta: Prazo próximo para o documento {doc.nome_arquivo}"
                        mensagem = f"O prazo para envio do documento '{doc.nome_arquivo}' termina em {dias_restantes} dia(s): {doc.prazo_limite.strftime('%d/%m/%Y')}. Por favor, envie o documento corrigido o quanto antes."
                        # CA5 - Referência única para evitar duplicidade
                        referencia = f"alerta_prazo_{doc.id}_{doc.prazo_limite}"
                        
                        # CA5 - Impede envio de notificações duplicadas
                        if not Notificacao.objects.filter(destinatario=destinatario, referencia=referencia).exists():
                            enviar_notificacao_email(destinatario=destinatario, assunto=assunto, mensagem=mensagem)
                            # CA6 - Registra data e hora do envio
                            Notificacao.objects.create(
                                destinatario=destinatario,
                                assunto=assunto,
                                mensagem=mensagem,
                                referencia=referencia,
                                data_envio=timezone.now()
                            )
                            notificacoes_enviadas += 1
                            # Registrar log de envio
                            logger.info(f"Notificação enviada para {destinatario} sobre documento {doc.id} - prazo: {doc.prazo_limite}")
                            self.stdout.write(self.style.SUCCESS(f"Notificação enviada para {destinatario} sobre documento {doc.id}"))
                        else:
                            logger.info(f"Notificação já enviada anteriormente para {destinatario} sobre documento {doc.id}")
                    except Aluno.DoesNotExist:
                        logger.warning(f"Aluno não encontrado para o estágio do documento {doc.id}")
                    except Exception as e:
                        logger.error(f"Erro ao notificar documento {doc.id}: {e}")
                        self.stdout.write(self.style.ERROR(f"Erro ao notificar documento {doc.id}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Total de notificações enviadas: {notificacoes_enviadas}"))
