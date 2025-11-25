from django.core.management.base import BaseCommand
from estagio.models import Documento, Aluno
from django.db import transaction

class Command(BaseCommand):
    help = 'Corrige a relação entre alunos e estágios baseado nos documentos enviados'

    def handle(self, *args, **options):
        documentos_corrigidos = 0
        documentos_sem_enviado_por = 0
        
        with transaction.atomic():
            # Para cada documento que tem enviado_por (usuário que enviou)
            for doc in Documento.objects.all():
                if doc.enviado_por:
                    try:
                        # Busca o aluno pelo usuário que enviou
                        aluno = Aluno.objects.get(usuario=doc.enviado_por)
                        
                        # Verifica se o aluno já está vinculado ao estágio
                        if aluno.estagio != doc.estagio:
                            aluno.estagio = doc.estagio
                            aluno.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Documento {doc.id}: Aluno {aluno.matricula} vinculado ao estágio {doc.estagio.id}'
                                )
                            )
                            documentos_corrigidos += 1
                        else:
                            self.stdout.write(f'- Documento {doc.id}: Aluno {aluno.matricula} já vinculado')
                    except Aluno.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠ Documento {doc.id}: Usuário {doc.enviado_por.username} não é um aluno'
                            )
                        )
                else:
                    documentos_sem_enviado_por += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Documento {doc.id}: Não possui campo enviado_por preenchido'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Correção concluída! {documentos_corrigidos} aluno(s) vinculado(s) aos estágios.'
            )
        )
        if documentos_sem_enviado_por > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ {documentos_sem_enviado_por} documento(s) sem campo enviado_por (precisam ser corrigidos manualmente)'
                )
            )
