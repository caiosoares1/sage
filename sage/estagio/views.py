
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib import messages
from django.http import JsonResponse
from admin.models import CursoCoordenador,Supervisor
from .forms import EstagioForm, DocumentoForm, AlunoCadastroForm, HorasCumpridasForm, SupervisorAlunoSelectForm
from .models import Estagio, Documento, DocumentoHistorico, HorasCumpridas, Notificacao, FeedbackSupervisor
from users.models import Usuario
from estagio.models import Aluno
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal, InvalidOperation
from utils.email import enviar_notificacao_email
from django.utils.dateparse import parse_date
from utils.decorators import aluno_required, supervisor_required
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@login_required
@aluno_required
def solicitar_estagio(request):
    """
    View para aluno solicitar estágio criando uma nova vaga.
    O aluno preenche os dados da vaga e envia o documento.
    O vínculo só acontece após aprovação do coordenador.
    """
    if request.method == "POST":
        estagio_form = EstagioForm(request.POST)
        documento_form = DocumentoForm(request.POST, request.FILES)

        # Valida os dois formulários
        if estagio_form.is_valid() and documento_form.is_valid():
            # Salva estágio com status inicial "Em análise"
            estagio = estagio_form.save(commit=False)
            estagio.status = "analise"
            estagio.status_vaga = "disponivel"  # Vaga fica disponível até aprovação
            
            try:
                usuario = Usuario.objects.get(id=request.user.id)
                aluno = Aluno.objects.get(usuario=usuario)
                estagio.aluno_solicitante = aluno  # Salva o aluno que solicitou
                estagio.save()
                
                # NÃO vincula o aluno automaticamente!
                # O vínculo só acontece quando o coordenador aprovar
                # aluno.estagio = estagio  # REMOVIDO
                # aluno.save()  # REMOVIDO
                
            except (Usuario.DoesNotExist, Aluno.DoesNotExist):
                messages.error(request, "Erro: Aluno não encontrado.")
                return redirect("solicitar_estagio")

            # Recupera o coordenador selecionado no form
            coordenador = documento_form.cleaned_data['coordenador']

            # Vincula o documento ao estágio
            documento = documento_form.save(commit=False)
            documento.data_envio = now().date()
            documento.estagio = estagio
            documento.supervisor = estagio.supervisor
            documento.coordenador = coordenador
            documento.versao = 1.0
            documento.tipo = 'termo_compromisso'
            documento.nome_arquivo = documento.arquivo.name if documento.arquivo else 'documento.pdf'
            documento.enviado_por = usuario
            documento.save()
            
            # Registrar no histórico
            DocumentoHistorico.objects.create(
                documento=documento,
                acao='enviado',
                usuario=usuario,
                observacoes="Documento inicial enviado"
            )

            # Enviar notificação para o coordenador
            coordenador_email = coordenador.usuario.email if coordenador.usuario.email else 'coordenador@example.com'
            aluno_email = aluno.contato if aluno.contato else None
            enviar_notificacao_email(
                destinatario=aluno_email or coordenador_email,
                assunto=f"Novo documento enviado pelo aluno {aluno.nome}",
                mensagem=f"O aluno {aluno.nome} enviou um novo documento para o estágio '{estagio.titulo}'. Por favor, revise o documento."
            )
            
            messages.success(request, "Solicitação enviada com sucesso! Aguarde a análise do coordenador.")
            return redirect("estagio_detalhe", estagio_id=estagio.id)
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")

    else:
        estagio_form = EstagioForm()
        documento_form = DocumentoForm()

    return render(request, "estagio/solicitar_estagio.html", {
        "estagio_form": estagio_form,
        "documento_form": documento_form
    })



@login_required
@aluno_required
def acompanhar_estagios(request):
    """View para listar as solicitações de estágio do aluno logado"""  
    try:
        # Busca o usuário logado
        usuario = Usuario.objects.get(id=request.user.id)
        # Busca o aluno vinculado a este usuário
        aluno = Aluno.objects.get(usuario=usuario)
        
        # Como Aluno tem FK para Estagio, verificamos se existe estágio vinculado
        if aluno.estagio:
            estagio = aluno.estagio
            estagios = [estagio]
            
            # Buscar estatísticas dos documentos do estágio
            documentos = Documento.objects.filter(estagio=estagio)
            stats = {
                'total': documentos.count(),
                'enviados': documentos.filter(status='enviado').count(),
                'aprovados_supervisor': documentos.filter(status='aprovado').count(),
                'finalizados': documentos.filter(status='finalizado').count(),
                'reprovados': documentos.filter(status='reprovado').count(),
                'ajustes': documentos.filter(status='ajustes_solicitados').count(),
            }
        else:
            estagios = []
            stats = {}
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        estagios = []
        stats = {}
    
    return render(request, "estagio/acompanhar_estagios.html", {
        "estagios": estagios,
        "stats": stats
    })


@login_required
@aluno_required
def historico_solicitacoes(request):
    """View para listar o histórico de todas as solicitações de estágio do aluno"""
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        
        from django.db.models import Q
        
        # Buscar todos os estágios relacionados ao aluno:
        # 1. Usando o novo campo aluno_solicitante
        # 2. Usando a relação inversa aluno_set (estágios que têm este aluno vinculado)
        solicitacoes = Estagio.objects.filter(
            Q(aluno_solicitante=aluno) | Q(aluno__id=aluno.id)
        ).select_related('empresa', 'supervisor').distinct().order_by('-id')
        
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        solicitacoes = []
    
    return render(request, "estagio/historico_solicitacoes.html", {
        "solicitacoes": solicitacoes
    })


@login_required
@aluno_required
def estagio_detalhe(request, estagio_id):
    """View para exibir detalhes de um estágio"""
    estagio = get_object_or_404(Estagio, id=estagio_id)
    
    # Buscar apenas a versão mais recente de cada documento (documentos que não têm filhos)
    documentos = Documento.objects.filter(
        estagio=estagio,
        versions__isnull=True  # Não tem filhos = é a versão mais recente
    ).select_related('aprovado_por').order_by('-created_at')
    
    return render(request, "estagio/estagio_detalhe.html", {
        "estagio": estagio,
        "documentos": documentos
    })


@login_required
def historico_estagio(request, estagio_id):
    """View para visualizar o histórico completo de todos os documentos de um estágio"""
    estagio = get_object_or_404(Estagio, id=estagio_id)
    
    # Verificar permissão - aluno, supervisor ou coordenador
    usuario = Usuario.objects.get(id=request.user.id)
    tem_permissao = False
    
    try:
        aluno = Aluno.objects.get(usuario=usuario)
        if estagio == aluno.estagio:
            tem_permissao = True
    except Aluno.DoesNotExist:
        pass
    
    try:
        supervisor = Supervisor.objects.get(usuario=usuario)
        if estagio.supervisor == supervisor:
            tem_permissao = True
    except Supervisor.DoesNotExist:
        pass
    
    try:
        coordenador = CursoCoordenador.objects.get(usuario=usuario)
        # Verifica se coordenador tem permissão sobre algum documento deste estágio
        if Documento.objects.filter(estagio=estagio, coordenador=coordenador).exists():
            tem_permissao = True
    except CursoCoordenador.DoesNotExist:
        pass
    
    if not tem_permissao:
        messages.error(request, "Você não tem permissão para visualizar este histórico.")
        return redirect('dashboard')
    
    # Buscar todos os documentos do estágio
    todos_documentos = Documento.objects.filter(estagio=estagio).select_related('aprovado_por', 'enviado_por')
    
    # Agrupar documentos por tipo (usando a raiz de cada cadeia)
    documentos_por_tipo = {}
    for doc in todos_documentos:
        tipo = doc.tipo
        if tipo not in documentos_por_tipo:
            documentos_por_tipo[tipo] = []
        documentos_por_tipo[tipo].append(doc)
    
    # Buscar histórico de todos os documentos
    todos_ids = [doc.id for doc in todos_documentos]
    historico = DocumentoHistorico.objects.filter(
        documento_id__in=todos_ids
    ).select_related('usuario', 'documento').order_by('-data_hora')
    
    context = {
        'estagio': estagio,
        'documentos_por_tipo': documentos_por_tipo,
        'historico': historico,
        'todos_documentos': todos_documentos,
    }
    
    return render(request, "estagio/historico_estagio.html", context)


@login_required
@aluno_required
def listar_documentos(request):
    """View para listar todos os documentos enviados pelo aluno"""
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        
        # Buscar todos os documentos relacionados aos estágios do aluno
        # Filtrar apenas a versão mais recente de cada cadeia (documentos que não têm filhos)
        if aluno.estagio:
            # Buscar apenas documentos que são a versão mais recente (não têm filhos)
            documentos = Documento.objects.filter(
                estagio=aluno.estagio,
                versions__isnull=True  # Não tem filhos = é a versão mais recente
            ).select_related('aprovado_por').order_by('-created_at')
        else:
            documentos = []
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        documentos = []
    
    return render(request, "estagio/listar_documentos.html", {"documentos": documentos})


@login_required
@aluno_required
def download_documento(request, documento_id):
    """View para fazer download de um documento"""
    documento = get_object_or_404(Documento, id=documento_id)
    
    # Verificar se o usuário tem permissão para baixar
    usuario = Usuario.objects.get(id=request.user.id)
    try:
        aluno = Aluno.objects.get(usuario=usuario)
        if documento.estagio != aluno.estagio:
            messages.error(request, "Você não tem permissão para acessar este documento.")
            return redirect("listar_documentos")
    except Aluno.DoesNotExist:
        # Verificar se é supervisor ou coordenador
        pass
    
    from django.http import FileResponse
    return FileResponse(documento.arquivo.open('rb'), as_attachment=True, filename=documento.nome_arquivo)


@login_required
@aluno_required
def historico_documento(request, documento_id):
    """View para visualizar o histórico completo de um documento"""
    try:
        # Busca o documento
        documento = get_object_or_404(
            Documento.objects.select_related(
                'estagio__empresa',
                'estagio__supervisor',
                'coordenador__usuario',
                'aprovado_por',
                'enviado_por'
            ).prefetch_related(
                'estagio__aluno_set__usuario'
            ),
            id=documento_id
        )
        
        # Verificar permissão - aluno, supervisor ou coordenador
        usuario = Usuario.objects.get(id=request.user.id)
        tem_permissao = False
        
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            if documento.estagio == aluno.estagio:
                tem_permissao = True
        except Aluno.DoesNotExist:
            pass
        
        try:
            supervisor = Supervisor.objects.get(usuario=usuario)
            if documento.estagio.supervisor == supervisor:
                tem_permissao = True
        except Supervisor.DoesNotExist:
            pass
        
        try:
            coordenador = CursoCoordenador.objects.get(usuario=usuario)
            if documento.coordenador == coordenador:
                tem_permissao = True
        except CursoCoordenador.DoesNotExist:
            pass
        
        if not tem_permissao:
            messages.error(request, "Você não tem permissão para visualizar este histórico.")
            return redirect('dashboard')
        
        # Obter toda a cadeia de versões (do mais antigo ao mais recente)
        versoes = documento.get_full_history()
        
        # Usar a versão mais recente como documento principal para exibição
        documento_atual = versoes[-1] if versoes else documento
        
        # Buscar histórico de todas as versões na cadeia
        from django.db.models import Q
        versoes_ids = [v.id for v in versoes]
        historico = DocumentoHistorico.objects.filter(
            documento_id__in=versoes_ids
        ).select_related('usuario', 'documento').order_by('-data_hora')
        
        context = {
            'documento': documento_atual,
            'historico': historico,
            'versoes': versoes
        }
        return render(request, "estagio/historico_documento.html", context)
        
    except Usuario.DoesNotExist:
        messages.error(request, "Erro: Usuário não encontrado.")
        return redirect('dashboard')


@login_required
@supervisor_required
def supervisor_requerir_ajustes(request, documento_id):
    """Supervisor solicita ajustes em um documento.

    GET: exibe formulário de observações.
    POST: salva observações, altera status e redireciona com mensagem.
    """
    # checar se usuário é supervisor
    if not Supervisor.objects.filter(usuario=getattr(request.user, 'id', request.user)).exists():
        messages.error(request, "Permissão negada.")
        return redirect("acompanhar_estagios")

    doc = get_object_or_404(Documento, pk=documento_id)

    if request.method == "POST":
        observacoes = request.POST.get('observacoes', '').strip()
        prazo_str = request.POST.get('prazo', '').strip()
        prazo_date = None
        if prazo_str:
            prazo_date = parse_date(prazo_str)
            if prazo_date is None:
                messages.error(request, "Formato de data inválido para o prazo. Use YYYY-MM-DD.")
                return redirect("estagio_detalhe", estagio_id=doc.estagio.id)

        doc.status = 'ajustes_solicitados'
        if observacoes:
            doc.observacoes_supervisor = observacoes
        # atribuir prazo_limite se informado
        if prazo_date:
            doc.prazo_limite = prazo_date

        # salvar campos relevantes
        doc.save(update_fields=['status', 'observacoes_supervisor', 'prazo_limite', 'updated_at'])

        # notificar por e-mail o usuário que enviou o documento com a data limite
        recipient = None
        try:
            aluno = Aluno.objects.get(estagio=doc.estagio)
            if aluno and aluno.usuario and aluno.usuario.email:
                recipient = aluno.usuario.email
        except Exception:
            recipient = None

        subject = f"Ajustes solicitados: {doc.nome_arquivo} - prazo estabelecido"
        prazo_text = prazo_date.strftime('%d/%m/%Y') if prazo_date else 'sem prazo definido'
        message = (
            f"Seu documento '{doc.nome_arquivo}' recebeu solicitação de ajustes pelo supervisor.\n\n"
            f"Prazo para envio das correções: {prazo_text}.\n\n"
            f"Observações:\n{doc.observacoes_supervisor or 'Nenhuma observação.'}\n\n"
            "Por favor, reenvie o documento até o prazo informado para evitar atraso."
        )
        if recipient:
            try:
                enviar_notificacao_email(destinatario=recipient, assunto=subject, mensagem=message)
                # Criar notificação no sistema
                try:
                    Notificacao.objects.get_or_create(
                        destinatario=recipient,
                        assunto=subject,
                        referencia=f"doc_ajustes_{doc.id}",
                        defaults={'mensagem': message}
                    )
                except Exception as e:
                    logger.warning(f"Erro ao criar notificação: {str(e)}")
            except Exception:
                pass

        messages.success(request, "Ajustes solicitados com sucesso e prazo enviado ao aluno.")
        return redirect("estagio_detalhe", estagio_id=doc.estagio.id)

    # GET: renderiza formulário simples para inserir observações e prazo
    return render(request, "estagio/supervisor_requerir_ajustes.html", {
        "documento": doc,
        "observacoes_iniciais": doc.observacoes_supervisor or "",
        "prazo_inicial": doc.prazo_limite.isoformat() if getattr(doc, 'prazo_limite', None) else "",
    })


@login_required
@transaction.atomic
def supervisor_aprovar_documento(request, documento_id):
    """Aprovar documento: registra supervisor, define status e notifica o aluno."""
    try:
        supervisor_obj = Supervisor.objects.get(usuario=request.user)
    except Supervisor.DoesNotExist:
        messages.error(request, "Permissão negada.")
        return redirect("acompanhar_estagios")

    doc = get_object_or_404(Documento, pk=documento_id)

    if request.method == 'POST':
        doc.status = 'aprovado'
        doc.supervisor = supervisor_obj
        doc.save()

        # registrar validação como um Documento filho (histórico)
        try:
            Documento.objects.create(
                data_envio=now().date(),
                versao=doc.versao,
                nome_arquivo=doc.nome_arquivo,
                tipo=doc.tipo,
                arquivo=doc.arquivo,
                estagio=doc.estagio,
                supervisor=supervisor_obj,
                coordenador=doc.coordenador,
                parent=doc,
                status='aprovado',
                observacoes_supervisor=None,
                enviado_por=doc.enviado_por,
            )
        except Exception:
            pass

        # descobrir destinatário
        recipient_email = None
        try:
            aluno = Aluno.objects.get(estagio=doc.estagio)
            if aluno and aluno.usuario and aluno.usuario.email:
                recipient_email = aluno.usuario.email
        except Exception:
            recipient_email = None

        if recipient_email:
            assunto = f"Documento aprovado: {doc.nome_arquivo}"
            mensagem = (
                f"Seu documento '{doc.nome_arquivo}' foi aprovado pelo supervisor {supervisor_obj.nome}.\n\n"
                "Acesse o sistema para mais informações."
            )
            enviar_notificacao_email(
                destinatario=recipient_email,
                assunto=assunto,
                mensagem=mensagem,
            )
            # Criar notificação no sistema
            try:
                Notificacao.objects.get_or_create(
                    destinatario=recipient_email,
                    assunto=assunto,
                    referencia=f"doc_aprovado_{doc.id}",
                    defaults={'mensagem': mensagem}
                )
            except Exception as e:
                logger.warning(f"Erro ao criar notificação: {str(e)}")

        messages.success(request, "Documento aprovado com sucesso.")
        return redirect('estagio_detalhe', estagio_id=doc.estagio.id)

    return render(request, 'estagio/aprovar_documento.html', {'documento': doc})


@login_required
@transaction.atomic
def supervisor_reprovar_documento(request, documento_id):
    """Reprovar documento: registra supervisor, salva observações e notifica o aluno."""
    try:
        supervisor_obj = Supervisor.objects.get(usuario=request.user)
    except Supervisor.DoesNotExist:
        messages.error(request, "Permissão negada.")
        return redirect("acompanhar_estagios")

    doc = get_object_or_404(Documento, pk=documento_id)

    if request.method == 'POST':
        observacoes = request.POST.get('observacoes', '').strip()
        doc.status = 'reprovado'
        doc.supervisor = supervisor_obj
        if observacoes:
            doc.observacoes_supervisor = observacoes
        doc.save()

        # registrar validação como um Documento filho (histórico)
        try:
            Documento.objects.create(
                data_envio=now().date(),
                versao=doc.versao,
                nome_arquivo=doc.nome_arquivo,
                tipo=doc.tipo,
                arquivo=doc.arquivo,
                estagio=doc.estagio,
                supervisor=supervisor_obj,
                coordenador=doc.coordenador,
                parent=doc,
                status='reprovado',
                observacoes_supervisor=observacoes or None,
                enviado_por=doc.enviado_por,
            )
        except Exception:
            pass

        # descobrir destinatário
        recipient_email = None
        try:
            aluno = Aluno.objects.get(estagio=doc.estagio)
            if aluno and aluno.usuario and aluno.usuario.email:
                recipient_email = aluno.usuario.email
        except Exception:
            recipient_email = None

        if recipient_email:
            assunto = f"Documento reprovado: {doc.nome_arquivo}"
            mensagem = f"Seu documento '{doc.nome_arquivo}' foi reprovado pelo supervisor {supervisor_obj.nome}.\n\n"
            if observacoes:
                mensagem += f"Observações:\n{observacoes}\n\n"
            mensagem += "Por favor, acesse o sistema para mais detalhes."
            enviar_notificacao_email(destinatario=recipient_email, assunto=assunto, mensagem=mensagem)
            # Criar notificação no sistema
            try:
                Notificacao.objects.get_or_create(
                    destinatario=recipient_email,
                    assunto=assunto,
                    referencia=f"doc_reprovado_{doc.id}",
                    defaults={'mensagem': mensagem}
                )
            except Exception as e:
                logger.warning(f"Erro ao criar notificação: {str(e)}")

        messages.success(request, "Documento reprovado e observações registradas.")
        return redirect('estagio_detalhe', estagio_id=doc.estagio.id)

    return render(request, 'estagio/reprovar_documento.html', {'documento': doc})


@login_required
@transaction.atomic
def supervisor_validar_documento(request, documento_id):
    """Endpoint genérico para validar (aprovar, solicitar ajustes, reprovar).

    Recebe `action` no POST: 'approve' | 'request_changes' | 'reject'.
    Registra uma entrada como um `Documento` filho (histórico) e notifica o aluno.
    """
    try:
        supervisor_obj = Supervisor.objects.get(usuario=request.user)
    except Supervisor.DoesNotExist:
        messages.error(request, "Permissão negada.")
        return redirect('acompanhar_estagios')

    doc = get_object_or_404(Documento, pk=documento_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        observacoes = request.POST.get('observacoes', '').strip()

        if action == 'approve':
            doc.status = 'aprovado'
            acao = 'aprovado'
        elif action == 'request_changes':
            doc.status = 'ajustes_solicitados'
            acao = 'ajustes_solicitados'
        elif action == 'reject':
            doc.status = 'reprovado'
            acao = 'reprovado'
        else:
            messages.error(request, 'Ação inválida.')
            return redirect('estagio_detalhe', estagio_id=doc.estagio.id)

        doc.supervisor = supervisor_obj
        if observacoes:
            doc.observacoes_supervisor = observacoes
        doc.save()

        # registrar validação como Documento filho (histórico)
        try:
            Documento.objects.create(
                data_envio=now().date(),
                versao=doc.versao,
                nome_arquivo=doc.nome_arquivo,
                tipo=doc.tipo,
                arquivo=doc.arquivo,
                estagio=doc.estagio,
                supervisor=supervisor_obj,
                coordenador=doc.coordenador,
                parent=doc,
                status=acao,
                observacoes_supervisor=observacoes or None,
                enviado_por=doc.enviado_por,
            )
        except Exception:
            pass

        # notificar aluno/remetente
        recipient = None
        try:
            aluno = Aluno.objects.get(estagio=doc.estagio)
            if aluno and aluno.usuario and aluno.usuario.email:
                recipient = aluno.usuario.email
        except Exception:
            recipient = None

        if recipient:
            assunto = f"Resultado da validação do documento: {doc.nome_arquivo}"
            texto = f"Seu documento '{doc.nome_arquivo}' foi {acao} pelo supervisor {supervisor_obj.nome}.\n\n"
            if observacoes:
                texto += f"Observações:\n{observacoes}\n\n"
            texto += "Acesse o sistema para mais detalhes."
            enviar_notificacao_email(destinatario=recipient, assunto=assunto, mensagem=texto)
            # Criar notificação no sistema
            try:
                Notificacao.objects.get_or_create(
                    destinatario=recipient,
                    assunto=assunto,
                    referencia=f"doc_{acao}_{doc.id}",
                    defaults={'mensagem': texto}
                )
            except Exception as e:
                logger.warning(f"Erro ao criar notificação: {str(e)}")

        messages.success(request, f"Documento {acao} com sucesso.")
        return redirect('estagio_detalhe', estagio_id=doc.estagio.id)

    # GET: renderiza formulário de validação
    return render(request, 'estagio/validar_documento.html', {'documento': doc})


@login_required
def documento_validacoes(request, documento_id):
    """Exibe o histórico de validações para um documento específico."""
    # checar permissão: supervisor ou aluno dono do estagio
    doc = get_object_or_404(Documento, pk=documento_id)

    # obter lista de validações relacionadas
    validacoes = doc.validacoes.order_by('-criado_em') if hasattr(doc, 'validacoes') else []

    return render(request, 'estagio/documento_validacoes.html', {'documento': doc, 'validacoes': validacoes})


@login_required
@transaction.atomic
def aluno_reenviar_documento(request, documento_id):
    """
    Aluno reenvia documento corrigido.
    - Valida que o usuário logado é o aluno responsável pelo estágio.
    - Permite reenvio apenas se o documento estiver em estado que requer ajustes/reprovação.
    - No POST cria nova versão do Documento (parent => old) e marca o antigo como 'substituido'.
    """
    old = get_object_or_404(Documento, pk=documento_id)

    # validar que o usuário logado é o aluno responsável pelo estágio do documento
    try:
        usuario_obj = Usuario.objects.get(pk=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario_obj)

        # agora usamos a variável aluno corretamente:
        if aluno.estagio != old.estagio:
            messages.error(request, "Permissão negada - você não pertence ao estágio deste documento.")
            return redirect("acompanhar_estagios")

    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        messages.error(request, "Permissão negada - não é aluno vinculado a este estágio.")
        return redirect("acompanhar_estagios")

    # permitir reenvio somente se o documento foi reprovado ou ajustes foram solicitados
    allowed_statuses = {'ajustes_solicitados', 'reprovado'}
    if str(old.status).lower() not in allowed_statuses:
        messages.error(request, "Reenvio não permitido: o documento não está em estado de ajustes/reprovação.")
        return redirect("estagio_detalhe", estagio_id=old.estagio.id)

    # POST: criar nova versão do documento
    if request.method == "POST":
        uploaded_file = request.FILES.get('arquivo')
        if not uploaded_file:
            messages.error(request, "Arquivo não enviado.")
            return redirect("estagio_detalhe", estagio_id=old.estagio.id)

        nome_arquivo = request.POST.get('nome_arquivo', uploaded_file.name or old.nome_arquivo)
        tipo = request.POST.get('tipo', old.tipo)

        # calcular nova versão
        try:
            old_versao = Decimal(str(old.versao)) if old.versao is not None else Decimal('0')
            new_version = old_versao + Decimal('1.0')
        except (InvalidOperation, TypeError):
            new_version = Decimal('1.0')

        # criar a nova versão do documento
        new_doc = Documento.objects.create(
            data_envio=now().date(),
            versao=float(new_version),
            nome_arquivo=nome_arquivo,
            tipo=tipo,
            arquivo=uploaded_file,
            estagio=old.estagio,
            supervisor=old.supervisor,
            coordenador=old.coordenador,
            parent=old,
            status='enviado',
            enviado_por=usuario_obj,
        )

        # marcar documento antigo como substituído
        old.status = 'substituido'
        try:
            old.save(update_fields=['status', 'updated_at'])
        except Exception:
            old.save()

        messages.success(request, f"Documento reenviado como nova versão (v{new_doc.versao}).")
        return redirect("estagio_detalhe", estagio_id=new_doc.estagio.id)

    # GET: renderizar formulário de reenvio
    return render(request, "estagio/aluno_reenviar_documento.html", {
        "documento": old
    })


@login_required
@aluno_required
def reenviar_documento(request, documento_id):
    """Permite ao aluno reenviar um documento após ajustes solicitados ou reprovação"""
    print(f"[DEBUG] reenviar_documento chamado - documento_id: {documento_id}, method: {request.method}")
    
    documento_original = get_object_or_404(Documento, id=documento_id)
    print(f"[DEBUG] Documento original encontrado: {documento_original.nome_arquivo}, status: {documento_original.status}")
    
    # Verificar se o documento pertence ao aluno logado
    try:
        aluno = request.user.aluno
        print(f"[DEBUG] Aluno: {aluno.matricula}, Estagio do doc: {documento_original.estagio.id}, Estagio do aluno: {aluno.estagio.id if aluno.estagio else 'None'}")
        
        if documento_original.estagio != aluno.estagio:
            messages.error(request, "Você não tem permissão para reenviar este documento.")
            return redirect('listar_documentos')
    except Aluno.DoesNotExist:
        print("[DEBUG] Aluno não existe")
        messages.error(request, "Aluno não encontrado.")
        return redirect('listar_documentos')
    
    # Verificar se o documento está em status que permite reenvio
    if documento_original.status not in ['ajustes_solicitados', 'reprovado']:
        print(f"[DEBUG] Status não permite reenvio: {documento_original.status}")
        messages.error(request, f"Este documento não pode ser reenviado. Status atual: {documento_original.status}")
        return redirect('listar_documentos')
    
    if request.method == "POST":
        print("[DEBUG] Método POST detectado")
        arquivo = request.FILES.get('arquivo')
        observacoes = request.POST.get('observacoes', '')
        print(f"[DEBUG] Arquivo recebido: {arquivo.name if arquivo else 'None'}, Observações: {observacoes}")
        
        if not arquivo:
            messages.error(request, "É necessário enviar um arquivo.")
            return redirect('listar_documentos')
        
        # Validar tamanho do arquivo (10MB)
        if arquivo.size > 10 * 1024 * 1024:
            messages.error(request, "O arquivo não pode ser maior que 10MB.")
            return redirect('listar_documentos')
        
        # Validar extensão
        extensao = arquivo.name.split('.')[-1].lower()
        if extensao not in ['pdf', 'doc', 'docx']:
            messages.error(request, "Formato de arquivo inválido. Use PDF, DOC ou DOCX.")
            return redirect('listar_documentos')
        
        try:
            with transaction.atomic():
                # Marcar documento original como substituído
                documento_original.status = 'substituido'
                documento_original.save()
                
                # Registrar no histórico
                DocumentoHistorico.objects.create(
                    documento=documento_original,
                    acao='corrigido',
                    usuario=request.user,
                    observacoes=f"Documento substituído por nova versão. {observacoes}"
                )
                
                # Criar novo documento com versão incrementada
                novo_documento = Documento.objects.create(
                    estagio=documento_original.estagio,
                    tipo=documento_original.tipo,
                    arquivo=arquivo,
                    nome_arquivo=arquivo.name,
                    data_envio=now().date(),
                    status='corrigido',  # Status 'corrigido' para reanálise
                    versao=documento_original.versao + 1,
                    supervisor=documento_original.supervisor,
                    coordenador=documento_original.coordenador,
                    enviado_por=request.user
                )
                
                # Registrar criação no histórico
                DocumentoHistorico.objects.create(
                    documento=novo_documento,
                    acao='corrigido',
                    usuario=request.user,
                    observacoes=f"Documento reenviado após correções (v{novo_documento.versao}). {observacoes}"
                )
                
                # Enviar notificação ao supervisor (não bloqueia se falhar)
                try:
                    if documento_original.supervisor and documento_original.supervisor.usuario:
                        nome_aluno = getattr(request.user, 'nome', None) or request.user.username
                        enviar_notificacao_email(
                            destinatario=documento_original.supervisor.usuario,
                            assunto=f"Documento Corrigido - {novo_documento.tipo}",
                            mensagem=f"O aluno {nome_aluno} reenviou o documento '{novo_documento.tipo}' após correções (versão {novo_documento.versao})."
                        )
                except Exception as email_error:
                    print(f"[AVISO] Erro ao enviar email de notificação: {email_error}")
                    # Continua normalmente mesmo se o email falhar
                
                messages.success(request, f"Documento reenviado com sucesso! Nova versão: v{novo_documento.versao}")
                return redirect('listar_documentos')
                
        except Exception as e:
            messages.error(request, f"Erro ao reenviar documento: {str(e)}")
            return redirect('listar_documentos')
    
    return redirect('listar_documentos')


def cadastrar_aluno(request):
    """View pública para cadastro de dados pessoais e acadêmicos do aluno.
    Permite que um usuário não autenticado se cadastre como aluno,
    ou que um usuário autenticado (sem outro perfil) complete seu cadastro.
    
    Supervisores e Coordenadores NÃO podem se cadastrar como alunos.
    """
    # Se usuário está autenticado, verificar se já tem perfil
    if request.user.is_authenticated:
        usuario = Usuario.objects.get(id=request.user.id)
        
        # Impedir supervisores e coordenadores de se cadastrarem como alunos
        if hasattr(request.user, 'supervisor'):
            messages.error(request, 'Supervisores não podem se cadastrar como alunos.')
            return redirect('dashboard')
        
        if hasattr(request.user, 'cursocoordenador'):
            messages.error(request, 'Coordenadores não podem se cadastrar como alunos.')
            return redirect('dashboard')
        
        # Verifica se o usuário já é aluno
        if Aluno.objects.filter(usuario=usuario).exists():
            messages.info(request, 'Você já possui um cadastro de aluno.')
            return redirect('editar_dados_aluno')
    else:
        usuario = None
    
    if request.method == 'POST':
        form = AlunoCadastroForm(request.POST)
        
        # Se não está logado, precisamos criar o usuário também
        if not request.user.is_authenticated:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('contato', '').strip()
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            
            # Validações de usuário
            if not username:
                messages.error(request, 'O nome de usuário é obrigatório.')
                return render(request, 'estagio/cadastrar_aluno.html', {'form': form, 'show_user_fields': True})
            
            if not password or len(password) < 6:
                messages.error(request, 'A senha deve ter pelo menos 6 caracteres.')
                return render(request, 'estagio/cadastrar_aluno.html', {'form': form, 'show_user_fields': True})
            
            if password != password_confirm:
                messages.error(request, 'As senhas não coincidem.')
                return render(request, 'estagio/cadastrar_aluno.html', {'form': form, 'show_user_fields': True})
            
            if Usuario.objects.filter(username=username).exists():
                messages.error(request, 'Este nome de usuário já está em uso.')
                return render(request, 'estagio/cadastrar_aluno.html', {'form': form, 'show_user_fields': True})
            
            if form.is_valid():
                # Criar usuário
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    tipo='aluno'
                )
                
                # Criar aluno
                aluno = form.save(commit=False)
                aluno.usuario = usuario
                aluno.save()
                
                # Fazer login automático
                from django.contrib.auth import login
                login(request, usuario)
                
                messages.success(request, 'Cadastro realizado com sucesso! Bem-vindo ao sistema.')
                return redirect('dashboard')
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
                return render(request, 'estagio/cadastrar_aluno.html', {'form': form, 'show_user_fields': True})
        else:
            # Usuário já está logado
            if form.is_valid():
                aluno = form.save(commit=False)
                aluno.usuario = usuario
                aluno.save()
                messages.success(request, 'Cadastro realizado com sucesso!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = AlunoCadastroForm()
    
    # Mostrar campos de usuário apenas se não estiver logado
    show_user_fields = not request.user.is_authenticated
    return render(request, 'estagio/cadastrar_aluno.html', {'form': form, 'show_user_fields': show_user_fields})


@login_required
@aluno_required
def editar_dados_aluno(request):
    usuario = Usuario.objects.get(id=request.user.id)
    aluno = get_object_or_404(Aluno, usuario=usuario)
    if request.method == 'POST':
        form = AlunoCadastroForm(request.POST, instance=aluno)
        # Bloqueio de edição do campo matrícula
        if 'matricula' in form.changed_data:
            form.add_error('matricula', 'Não é permitido alterar a matrícula.')
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('editar_dados_aluno')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = AlunoCadastroForm(instance=aluno)
        form.fields['matricula'].widget.attrs['readonly'] = True
    return render(request, 'estagio/editar_dados_aluno.html', {'form': form, 'aluno': aluno})


@login_required
@aluno_required
def cadastrar_horas(request):
    usuario = Usuario.objects.get(id=request.user.id)
    aluno = get_object_or_404(Aluno, usuario=usuario)
    # Parametriza a meta de horas obrigatórias conforme a carga_horaria do estágio
    if aluno.estagio and aluno.estagio.carga_horaria:
        horas_obrigatorias = aluno.estagio.carga_horaria
    else:
        horas_obrigatorias = 100  # fallback padrão se não houver estágio vinculado
    if request.method == 'POST':
        form = HorasCumpridasForm(request.POST)
        if form.is_valid():
            horas = form.save(commit=False)
            horas.aluno = aluno
            horas.save()
            total = HorasCumpridas.objects.filter(aluno=aluno).aggregate(total=Sum('quantidade'))['total'] or 0
            pendente = max(horas_obrigatorias - total, 0)
            messages.success(request, f'Horas cadastradas com sucesso! Total cumprido: {total}h. Horas pendentes: {pendente}h')
            return redirect('cadastrar_horas')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = HorasCumpridasForm()
    total = HorasCumpridas.objects.filter(aluno=aluno).aggregate(total=Sum('quantidade'))['total'] or 0
    pendente = max(horas_obrigatorias - total, 0)
    return render(request, 'estagio/cadastrar_horas.html', {'form': form, 'total_horas': total, 'horas_pendentes': pendente, 'horas_obrigatorias': horas_obrigatorias})




@login_required
@supervisor_required
def supervisor_ver_horas(request):
    aluno_selecionado = None
    horas_list = []
    total_horas = 0
    form = SupervisorAlunoSelectForm(request.GET or None)
    if form.is_valid():
        aluno_selecionado = form.cleaned_data['aluno']
        # CA3, CA8 - Lista detalhada, ordenação cronológica (mais recente primeiro)
        horas_list = HorasCumpridas.objects.filter(aluno=aluno_selecionado).order_by('-data')
        # CA2 - Total de horas
        total_horas = horas_list.aggregate(total=Sum('quantidade'))['total'] or 0

    context = {
        'form': form,
        'aluno_selecionado': aluno_selecionado,
        'horas_list': horas_list,
        'total_horas': total_horas,
    }
    return render(request, 'estagio/supervisor_ver_horas.html', context)


@login_required
def listar_notificacoes(request):
    """View para listar as notificações do usuário logado"""
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        # Busca o aluno vinculado ao usuário para obter o email
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            email_destinatario = aluno.usuario.email
        except Aluno.DoesNotExist:
            # Se não for aluno, tenta buscar como supervisor ou coordenador
            try:
                supervisor = Supervisor.objects.get(usuario=usuario)
                email_destinatario = supervisor.usuario.email
            except Supervisor.DoesNotExist:
                try:
                    coordenador = CursoCoordenador.objects.get(usuario=usuario)
                    email_destinatario = coordenador.usuario.email
                except CursoCoordenador.DoesNotExist:
                    email_destinatario = usuario.email
        
        # Busca notificações enviadas para o email do usuário
        notificacoes = Notificacao.objects.filter(destinatario=email_destinatario).order_by('-data_envio')
    except Usuario.DoesNotExist:
        notificacoes = []
    
    return render(request, 'estagio/listar_notificacoes.html', {'notificacoes': notificacoes})


@login_required
def marcar_notificacao_lida(request, notificacao_id):
    """Marca uma notificação como lida (exclui da lista)"""
    notificacao = get_object_or_404(Notificacao, id=notificacao_id)
    # Verifica se o usuário tem permissão
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            email_destinatario = aluno.contato
        except Aluno.DoesNotExist:
            try:
                supervisor = Supervisor.objects.get(usuario=usuario)
                email_destinatario = supervisor.contato
            except Supervisor.DoesNotExist:
                try:
                    coordenador = CursoCoordenador.objects.get(usuario=usuario)
                    email_destinatario = coordenador.contato
                except CursoCoordenador.DoesNotExist:
                    email_destinatario = usuario.email
        
        if notificacao.destinatario == email_destinatario:
            notificacao.delete()
            messages.success(request, 'Notificação removida com sucesso.')
        else:
            messages.error(request, 'Você não tem permissão para remover esta notificação.')
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
    
    return redirect('listar_notificacoes')


@login_required
def api_notificacoes(request):
    """API que retorna as notificações do usuário logado em formato JSON para o popup"""
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        # Busca o email do usuário conforme seu tipo
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            email_destinatario = aluno.contato
        except Aluno.DoesNotExist:
            try:
                supervisor = Supervisor.objects.get(usuario=usuario)
                email_destinatario = supervisor.contato
            except Supervisor.DoesNotExist:
                try:
                    coordenador = CursoCoordenador.objects.get(usuario=usuario)
                    email_destinatario = coordenador.contato
                except CursoCoordenador.DoesNotExist:
                    email_destinatario = usuario.email
        
        # Busca notificações enviadas para o email do usuário
        notificacoes = Notificacao.objects.filter(destinatario=email_destinatario).order_by('-data_envio')[:10]
        
        data = {
            'count': notificacoes.count(),
            'total': notificacoes.count(),
            'notificacoes': [
                {
                    'id': n.id,
                    'assunto': n.assunto,
                    'mensagem': n.mensagem,
                    'data_envio': n.data_envio.strftime('%d/%m/%Y %H:%M'),
                    'referencia': n.referencia
                } for n in notificacoes
            ]
        }
    except Usuario.DoesNotExist:
        data = {'count': 0, 'total': 0, 'notificacoes': []}
    
    return JsonResponse(data)


@login_required
def api_contar_notificacoes_nao_lidas(request):
    """API que retorna o número de notificações - para badge na navbar"""
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        # Busca o email do usuário conforme seu tipo
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            email_destinatario = aluno.contato
        except Aluno.DoesNotExist:
            try:
                supervisor = Supervisor.objects.get(usuario=usuario)
                email_destinatario = supervisor.contato
            except Supervisor.DoesNotExist:
                try:
                    coordenador = CursoCoordenador.objects.get(usuario=usuario)
                    email_destinatario = coordenador.contato
                except CursoCoordenador.DoesNotExist:
                    email_destinatario = usuario.email
        
        # Conta todas as notificações não deletadas
        count = Notificacao.objects.filter(destinatario=email_destinatario).count()
        
        return JsonResponse({'count': count})
    except Usuario.DoesNotExist:
        return JsonResponse({'count': 0})


@login_required
def api_marcar_notificacao_lida(request, notificacao_id):
    """API para marcar uma notificação como lida (remove) via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            email_destinatario = aluno.contato
        except Aluno.DoesNotExist:
            try:
                supervisor = Supervisor.objects.get(usuario=usuario)
                email_destinatario = supervisor.contato
            except Supervisor.DoesNotExist:
                try:
                    coordenador = CursoCoordenador.objects.get(usuario=usuario)
                    email_destinatario = coordenador.contato
                except CursoCoordenador.DoesNotExist:
                    email_destinatario = usuario.email
        
        notificacao = get_object_or_404(Notificacao, id=notificacao_id)
        
        if notificacao.destinatario == email_destinatario:
            notificacao.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuário não encontrado'}, status=404)


def verificar_prazos_proximos(dias_alerta=3):
    """Função utilitária para verificar e enviar notificações de prazos próximos
    CA1 - Identifica documentos com prazos próximos automaticamente
    CA2 - Envia notificação quando faltar o período mínimo definido
    CA3 - Notificação informa nome do documento e data limite
    CA4 - Não envia para documentos já entregues
    CA5 - Impede notificações duplicadas
    CA6 - Registra data e hora do envio
    """
    logger = logging.getLogger(__name__)
    
    hoje = timezone.now().date()
    notificacoes_enviadas = []
    
    # CA1 - Identifica documentos com prazos próximos
    # CA4 - Exclui documentos já entregues
    documentos = Documento.objects.filter(
        prazo_limite__isnull=False
    ).exclude(
        status__in=['aprovado', 'finalizado', 'substituido', 'enviado', 'corrigido']
    )
    
    for doc in documentos:
        if doc.prazo_limite:
            dias_restantes = (doc.prazo_limite - hoje).days
            # CA2 - Verifica se está dentro do período de alerta
            if 0 <= dias_restantes <= dias_alerta:
                try:
                    aluno = Aluno.objects.get(estagio=doc.estagio)
                    destinatario = aluno.contato
                    # CA3 - Informa nome do documento e data limite
                    assunto = f"Alerta: Prazo próximo para o documento {doc.nome_arquivo}"
                    mensagem = f"O prazo para envio do documento '{doc.nome_arquivo}' termina em {dias_restantes} dia(s): {doc.prazo_limite.strftime('%d/%m/%Y')}. Por favor, envie o documento corrigido o quanto antes."
                    # CA5 - Referência única para evitar duplicidade
                    referencia = f"alerta_prazo_{doc.id}_{doc.prazo_limite}"
                    
                    # CA5 - Impede notificações duplicadas
                    if not Notificacao.objects.filter(destinatario=destinatario, referencia=referencia).exists():
                        try:
                            enviar_notificacao_email(destinatario=destinatario, assunto=assunto, mensagem=mensagem)
                        except Exception:
                            pass  # Continua mesmo se email falhar
                        
                        # CA6 - Registra data e hora do envio
                        notificacao = Notificacao.objects.create(
                            destinatario=destinatario,
                            assunto=assunto,
                            mensagem=mensagem,
                            referencia=referencia,
                            data_envio=timezone.now()
                        )
                        notificacoes_enviadas.append(notificacao)
                        logger.info(f"Notificação enviada para {destinatario} sobre documento {doc.id}")
                except Aluno.DoesNotExist:
                    logger.warning(f"Aluno não encontrado para o estágio do documento {doc.id}")
                except Exception as e:
                    logger.error(f"Erro ao notificar documento {doc.id}: {e}")
    
    return notificacoes_enviadas


@login_required
def api_verificar_prazos(request):
    """API para verificar e enviar notificações de prazos próximos manualmente"""
    dias_alerta = int(request.GET.get('dias', 3))
    notificacoes = verificar_prazos_proximos(dias_alerta)
    return JsonResponse({
        'success': True,
        'notificacoes_enviadas': len(notificacoes),
        'detalhes': [
            {'id': n.id, 'destinatario': n.destinatario, 'assunto': n.assunto}
            for n in notificacoes
        ]
    })


@login_required
@aluno_required
def listar_feedbacks(request):
    """View para listar os feedbacks recebidos do supervisor pelo aluno logado
    Task 20939 - Criar tela de listagem de feedbacks
    Task 20940 - Exibir data, conteúdo e nome do supervisor
    Task 20943 - Exibir mensagem quando não houver feedbacks
    """
    from .models import FeedbackSupervisor
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        
        # Busca feedbacks do aluno ordenados por data (mais recente primeiro)
        feedbacks = FeedbackSupervisor.objects.filter(
            aluno=aluno
        ).select_related('supervisor', 'estagio').order_by('-data_feedback')
        
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        feedbacks = []
    
    return render(request, 'estagio/listar_feedbacks.html', {'feedbacks': feedbacks})


@login_required
@aluno_required
def consultar_horas(request):
    """View para o aluno consultar suas horas de estágio
    Task 20926 - Criar tela de consulta de carga horária
    Task 20928 - Listar horas registradas (data, quantidade e descrição)
    Task 20929 - Exibir mensagem quando não houver horas cadastradas
    """
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        
        # Busca horas do aluno ordenadas por data (mais recente primeiro)
        horas_list = HorasCumpridas.objects.filter(aluno=aluno).order_by('-data')
        total_horas = horas_list.aggregate(total=Sum('quantidade'))['total'] or 0
        
        # Calcula horas obrigatórias e pendentes
        if aluno.estagio and aluno.estagio.carga_horaria:
            horas_obrigatorias = aluno.estagio.carga_horaria
        else:
            horas_obrigatorias = 100  # fallback padrão
        
        horas_pendentes = max(horas_obrigatorias - total_horas, 0)
        
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        horas_list = []
        total_horas = 0
        horas_obrigatorias = 100
        horas_pendentes = 100
    
    return render(request, 'estagio/consultar_horas.html', {
        'horas_list': horas_list,
        'total_horas': total_horas,
        'horas_obrigatorias': horas_obrigatorias,
        'horas_pendentes': horas_pendentes
    })


# ============================================
# Feedback do Supervisor - Views (Tasks 20939-20943)
# ============================================

@login_required
@supervisor_required
def enviar_feedback_aluno(request, aluno_id=None):
    """View para o supervisor enviar feedback para um aluno específico.
    
    GET: Exibe lista de alunos supervisionados ou formulário para enviar feedback
    POST: Registra o feedback no banco de dados e notifica o aluno por email
    
    Task 20939 - Criar tela de envio de feedbacks
    Task 20940 - Registrar data e nome do supervisor
    Task 20943 - Enviar notificação por email ao aluno
    """
    try:
        supervisor_obj = Supervisor.objects.get(usuario=request.user)
    except Supervisor.DoesNotExist:
        messages.error(request, "Permissão negada. Você não é um supervisor.")
        return redirect('dashboard')
    
    # Se aluno_id fornecido, trata como POST (envio de feedback)
    if aluno_id and request.method == 'POST':
        try:
            aluno = Aluno.objects.get(id=aluno_id)
            # Verificar se o aluno está sob supervisão deste supervisor (via estagio do aluno)
            if not aluno.estagio or aluno.estagio.supervisor != supervisor_obj:
                messages.error(request, "Você não tem permissão para enviar feedback a este aluno.")
                return redirect('enviar_feedback_aluno')
            
            conteudo = request.POST.get('conteudo', '').strip()
            if not conteudo:
                messages.warning(request, "O feedback não pode estar vazio.")
                return render(request, 'estagio/enviar_feedback.html', {
                    'aluno': aluno,
                    'alunos_supervisionados': get_alunos_supervisionados(supervisor_obj),
                    'form_mode': 'edit'
                })
            
            estagio = aluno.estagio
            if not estagio:
                messages.error(request, "Nenhum estágio encontrado para este aluno.")
                return redirect('enviar_feedback_aluno')
            
            # Criar feedback
            feedback = FeedbackSupervisor.objects.create(
                aluno=aluno,
                supervisor=supervisor_obj,
                estagio=estagio,
                conteudo=conteudo
            )
            
            # Enviar notificação por email ao aluno
            try:
                email_aluno = aluno.contato or aluno.usuario.email
                if email_aluno:
                    assunto = f"Novo Feedback do Supervisor {supervisor_obj.nome}"
                    mensagem = (
                        f"Você recebeu um novo feedback do supervisor {supervisor_obj.nome}:\n\n"
                        f"Estágio: {estagio.titulo}\n"
                        f"Data: {feedback.data_feedback.strftime('%d/%m/%Y às %H:%M')}\n\n"
                        f"Feedback:\n{conteudo}\n\n"
                        "Acesse o sistema para visualizar seu histórico de feedbacks."
                    )
                    enviar_notificacao_email(
                        destinatario=email_aluno,
                        assunto=assunto,
                        mensagem=mensagem
                    )
                    
                    # Registrar notificação no banco
                    Notificacao.objects.get_or_create(
                        destinatario=email_aluno,
                        assunto=assunto,
                        referencia=f"feedback_{feedback.id}",
                        defaults={'mensagem': mensagem}
                    )
            except Exception as e:
                logger.warning(f"Erro ao enviar email de feedback: {str(e)}")
                messages.warning(request, "Feedback registrado, mas ocorreu erro ao enviar notificação por email.")
            
            messages.success(request, f"Feedback enviado com sucesso para {aluno.nome}.")
            return redirect('enviar_feedback_aluno')
            
        except Aluno.DoesNotExist:
            messages.error(request, "Aluno não encontrado.")
            return redirect('enviar_feedback_aluno')
    
    # GET: Exibir lista de alunos ou formulário
    if aluno_id:
        try:
            aluno = Aluno.objects.get(id=aluno_id)
            if not aluno.estagio or aluno.estagio.supervisor != supervisor_obj:
                messages.error(request, "Você não tem permissão para enviar feedback a este aluno.")
                return redirect('enviar_feedback_aluno')
            
            return render(request, 'estagio/enviar_feedback.html', {
                'aluno': aluno,
                'alunos_supervisionados': get_alunos_supervisionados(supervisor_obj),
                'form_mode': 'edit'
            })
        except Aluno.DoesNotExist:
            messages.error(request, "Aluno não encontrado.")
            return redirect('enviar_feedback_aluno')
    
    # Retornar lista de alunos supervisionados
    alunos_supervisionados = get_alunos_supervisionados(supervisor_obj)
    return render(request, 'estagio/enviar_feedback.html', {
        'alunos_supervisionados': alunos_supervisionados,
        'form_mode': 'select'
    })


def get_alunos_supervisionados(supervisor):
    """Retorna lista de alunos únicos supervisionados por este supervisor."""
    alunos = Aluno.objects.filter(
        estagio__supervisor=supervisor
    ).distinct().select_related('usuario', 'estagio')
    return alunos


# ==================== VIEWS DE CONSULTA DE PARECER - CA6 ====================

@login_required
@aluno_required
def listar_pareceres_aluno(request):
    """
    CA6 - View para aluno listar seus pareceres disponíveis para consulta.
    Lista todas as avaliações com parecer emitido e disponível para consulta.
    """
    from estagio.models import Avaliacao
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        
        # Busca avaliações com parecer disponível para consulta
        avaliacoes_com_parecer = Avaliacao.objects.filter(
            aluno=aluno,
            status='parecer_emitido',
            parecer_disponivel_consulta=True
        ).select_related(
            'supervisor',
            'estagio__empresa'
        ).order_by('-data_emissao_parecer')
        
        # Estatísticas
        total_pareceres = avaliacoes_com_parecer.count()
        if total_pareceres > 0:
            media_notas = sum(a.nota_final for a in avaliacoes_com_parecer if a.nota_final) / total_pareceres
        else:
            media_notas = None
        
        context = {
            'avaliacoes': avaliacoes_com_parecer,
            'aluno': aluno,
            'total_pareceres': total_pareceres,
            'media_notas': media_notas,
        }
        return render(request, 'estagio/listar_pareceres.html', context)
        
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        messages.error(request, "Aluno não encontrado!")
        return redirect('dashboard')


@login_required
@aluno_required
def consultar_parecer(request, avaliacao_id):
    """
    CA6 - View para aluno consultar o parecer final de uma avaliação específica.
    
    BDD:
    DADO que a avaliação foi concluída
    QUANDO o supervisor emitir o parecer final
    ENTÃO o sistema deve gerar a nota e o parecer do estagiário
    (Esta view permite a consulta pelo aluno após emissão)
    """
    from estagio.models import Avaliacao
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        
        # Busca avaliação garantindo que pertence ao aluno e está disponível
        avaliacao = get_object_or_404(
            Avaliacao.objects.select_related(
                'supervisor',
                'estagio__empresa'
            ).prefetch_related(
                'notas_criterios__criterio'
            ),
            id=avaliacao_id,
            aluno=aluno
        )
        
        # Verifica se o parecer foi emitido e está disponível
        if avaliacao.status != 'parecer_emitido':
            messages.warning(request, 'O parecer desta avaliação ainda não foi emitido.')
            return redirect('listar_pareceres_aluno')
        
        if not avaliacao.parecer_disponivel_consulta:
            messages.warning(request, 'O parecer desta avaliação não está disponível para consulta.')
            return redirect('listar_pareceres_aluno')
        
        # CA6 - Obtém dados do parecer para consulta
        parecer_dados = avaliacao.get_parecer_para_consulta()
        
        # Notas por critério (para exibição detalhada)
        notas_criterios = avaliacao.notas_criterios.all().order_by('criterio__ordem')
        
        context = {
            'avaliacao': avaliacao,
            'parecer_dados': parecer_dados,
            'notas_criterios': notas_criterios,
            'aluno': aluno,
        }
        return render(request, 'estagio/consultar_parecer.html', context)
        
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        messages.error(request, "Aluno não encontrado!")
        return redirect('dashboard')


# ==================== PAINEL DE STATUS DE ESTÁGIOS ====================

@login_required
def painel_estagios(request):
    """
    View para exibição do painel de status dos estágios.
    
    US: Visualização em painel dos status dos estágios
    CA1 - O sistema deve permitir a exibição de estágios por status
    CA3 - O sistema deve ter acesso restrito conforme perfil do usuário
    
    BDD:
    DADO que existem estágios cadastrados
    QUANDO o usuário acessar o painel
    ENTÃO deve visualizar o status atualizado dos estágios
    """
    usuario = request.user
    
    # CA3 - Controle de acesso por perfil
    estagios = _filtrar_estagios_por_perfil(usuario)
    
    # CA1 - Agrupamento por status
    estagios_por_status = _agrupar_estagios_por_status(estagios)
    
    # Estatísticas gerais
    estatisticas = _calcular_estatisticas_estagios(estagios)
    
    # Filtros aplicados
    filtro_status = request.GET.get('status', '')
    if filtro_status:
        estagios = estagios.filter(status=filtro_status)
    
    filtro_empresa = request.GET.get('empresa', '')
    if filtro_empresa:
        estagios = estagios.filter(empresa__razao_social__icontains=filtro_empresa)
    
    context = {
        'estagios': estagios.order_by('-data_solicitacao'),
        'estagios_por_status': estagios_por_status,
        'estatisticas': estatisticas,
        'status_choices': Estagio.STATUS_CHOICES,
        'filtro_status': filtro_status,
        'filtro_empresa': filtro_empresa,
        'perfil_usuario': usuario.tipo,
    }
    return render(request, 'estagio/painel_estagios.html', context)


@login_required
def api_painel_estagios(request):
    """
    API para atualização automática do painel de estágios.
    
    US: Visualização em painel dos status dos estágios
    CA2 - O sistema deve permitir a atualização automática das informações
    CA3 - O sistema deve ter acesso restrito conforme perfil do usuário
    
    Retorna dados JSON para atualização via AJAX/polling.
    """
    usuario = request.user
    
    # CA3 - Controle de acesso por perfil
    estagios = _filtrar_estagios_por_perfil(usuario)
    
    # CA1 - Agrupamento por status
    estagios_por_status = _agrupar_estagios_por_status(estagios)
    
    # Estatísticas
    estatisticas = _calcular_estatisticas_estagios(estagios)
    
    # CA2 - Dados para atualização automática
    dados = {
        'timestamp': timezone.now().isoformat(),
        'estatisticas': estatisticas,
        'estagios_por_status': {
            status: list(qs.values('id', 'titulo', 'status', 'empresa__razao_social', 'data_inicio', 'data_fim'))
            for status, qs in estagios_por_status.items()
        },
        'total_estagios': estagios.count(),
    }
    
    return JsonResponse(dados)


@login_required
def api_estatisticas_estagios(request):
    """
    API para obter estatísticas dos estágios em tempo real.
    
    CA2 - O sistema deve permitir a atualização automática das informações
    CA3 - O sistema deve ter acesso restrito conforme perfil do usuário
    """
    usuario = request.user
    
    # CA3 - Controle de acesso por perfil
    estagios = _filtrar_estagios_por_perfil(usuario)
    
    estatisticas = _calcular_estatisticas_estagios(estagios)
    estatisticas['timestamp'] = timezone.now().isoformat()
    
    return JsonResponse(estatisticas)


@login_required
def api_estagios_por_status(request, status):
    """
    API para obter estágios filtrados por status específico.
    
    CA1 - O sistema deve permitir a exibição de estágios por status
    CA2 - O sistema deve permitir a atualização automática das informações
    CA3 - O sistema deve ter acesso restrito conforme perfil do usuário
    """
    usuario = request.user
    
    # Valida status
    status_validos = [s[0] for s in Estagio.STATUS_CHOICES]
    if status not in status_validos:
        return JsonResponse({'error': 'Status inválido'}, status=400)
    
    # CA3 - Controle de acesso por perfil
    estagios = _filtrar_estagios_por_perfil(usuario)
    
    # CA1 - Filtra por status
    estagios_filtrados = estagios.filter(status=status)
    
    dados = {
        'status': status,
        'status_display': dict(Estagio.STATUS_CHOICES).get(status),
        'total': estagios_filtrados.count(),
        'estagios': list(estagios_filtrados.values(
            'id', 'titulo', 'cargo', 'empresa__razao_social',
            'data_inicio', 'data_fim', 'carga_horaria'
        )),
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(dados)


def _filtrar_estagios_por_perfil(usuario):
    """
    Função auxiliar para filtrar estágios conforme perfil do usuário.
    
    CA3 - O sistema deve ter acesso restrito conforme perfil do usuário
    
    Retorna:
    - Coordenador: todos os estágios
    - Supervisor: apenas estágios que supervisiona
    - Aluno: apenas seus próprios estágios
    """
    if usuario.tipo == 'coordenador':
        # Coordenador vê todos os estágios
        return Estagio.objects.all()
    
    elif usuario.tipo == 'supervisor':
        # Supervisor vê apenas estágios que supervisiona
        try:
            supervisor = Supervisor.objects.get(usuario=usuario)
            return Estagio.objects.filter(supervisor=supervisor)
        except Supervisor.DoesNotExist:
            return Estagio.objects.none()
    
    elif usuario.tipo == 'aluno':
        # Aluno vê apenas seus próprios estágios
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            return Estagio.objects.filter(aluno_solicitante=aluno)
        except Aluno.DoesNotExist:
            return Estagio.objects.none()
    
    # Perfil não reconhecido - sem acesso
    return Estagio.objects.none()


def _agrupar_estagios_por_status(estagios):
    """
    Função auxiliar para agrupar estágios por status.
    
    CA1 - O sistema deve permitir a exibição de estágios por status
    """
    return {
        'analise': estagios.filter(status='analise'),
        'em_andamento': estagios.filter(status='em_andamento'),
        'aprovado': estagios.filter(status='aprovado'),
        'reprovado': estagios.filter(status='reprovado'),
    }


def _calcular_estatisticas_estagios(estagios):
    """
    Função auxiliar para calcular estatísticas dos estágios.
    
    CA1 - Estatísticas por status para exibição no painel
    """
    total = estagios.count()
    
    estatisticas = {
        'total': total,
        'analise': estagios.filter(status='analise').count(),
        'em_andamento': estagios.filter(status='em_andamento').count(),
        'aprovado': estagios.filter(status='aprovado').count(),
        'reprovado': estagios.filter(status='reprovado').count(),
    }
    
    # Percentuais
    if total > 0:
        estatisticas['percentual_analise'] = round((estatisticas['analise'] / total) * 100, 1)
        estatisticas['percentual_em_andamento'] = round((estatisticas['em_andamento'] / total) * 100, 1)
        estatisticas['percentual_aprovado'] = round((estatisticas['aprovado'] / total) * 100, 1)
        estatisticas['percentual_reprovado'] = round((estatisticas['reprovado'] / total) * 100, 1)
    else:
        estatisticas['percentual_analise'] = 0
        estatisticas['percentual_em_andamento'] = 0
        estatisticas['percentual_aprovado'] = 0
        estatisticas['percentual_reprovado'] = 0
    
    return estatisticas


# ==================== MONITORAMENTO DE PENDÊNCIAS E RESULTADOS ====================

# Constantes para tipos de pendência
TIPOS_PENDENCIA = {
    'documento_pendente': {
        'nome': 'Documento Pendente',
        'descricao': 'Documentos aguardando envio ou correção',
        'critico': False,
    },
    'documento_ajuste': {
        'nome': 'Documento com Ajustes Solicitados',
        'descricao': 'Documentos que precisam de correção',
        'critico': True,
    },
    'documento_prazo': {
        'nome': 'Documento com Prazo Próximo',
        'descricao': 'Documentos com prazo de vencimento próximo',
        'critico': True,
    },
    'avaliacao_pendente': {
        'nome': 'Avaliação Pendente',
        'descricao': 'Avaliações aguardando preenchimento',
        'critico': False,
    },
    'avaliacao_incompleta': {
        'nome': 'Avaliação Incompleta',
        'descricao': 'Avaliações com critérios não preenchidos',
        'critico': True,
    },
    'estagio_analise': {
        'nome': 'Estágio em Análise',
        'descricao': 'Estágios aguardando aprovação',
        'critico': False,
    },
    'horas_insuficientes': {
        'nome': 'Horas Insuficientes',
        'descricao': 'Alunos com horas abaixo do esperado',
        'critico': True,
    },
}


@login_required
def monitoramento_pendencias(request):
    """
    View para monitoramento de pendências e resultados consolidados.
    
    US: Monitoramento de pendências e resultados
    CA4 - O sistema deve permitir a exibição de pendências por tipo
    CA5 - O sistema deve ter um destaque visual para pendências críticas
    CA6 - O sistema deve permitir a visualização de resultados consolidados
    
    BDD:
    DADO que há pendências e resultados registrados
    QUANDO o usuário acessar o monitoramento
    ENTÃO deve visualizar alertas e resultados consolidados
    """
    usuario = request.user
    
    # CA4 - Obtém pendências agrupadas por tipo
    pendencias = _obter_pendencias_por_perfil(usuario)
    pendencias_por_tipo = _agrupar_pendencias_por_tipo(pendencias)
    
    # CA5 - Identifica pendências críticas
    pendencias_criticas = _filtrar_pendencias_criticas(pendencias)
    
    # CA6 - Resultados consolidados
    resultados_consolidados = _consolidar_resultados(usuario)
    
    # Filtro por tipo de pendência
    filtro_tipo = request.GET.get('tipo', '')
    if filtro_tipo and filtro_tipo in TIPOS_PENDENCIA:
        pendencias = [p for p in pendencias if p['tipo'] == filtro_tipo]
    
    # Filtro por criticidade
    filtro_critico = request.GET.get('critico', '')
    if filtro_critico == 'true':
        pendencias = [p for p in pendencias if p['critico']]
    
    context = {
        'pendencias': pendencias,
        'pendencias_por_tipo': pendencias_por_tipo,
        'pendencias_criticas': pendencias_criticas,
        'resultados_consolidados': resultados_consolidados,
        'tipos_pendencia': TIPOS_PENDENCIA,
        'filtro_tipo': filtro_tipo,
        'filtro_critico': filtro_critico,
        'total_pendencias': len(pendencias),
        'total_criticas': len(pendencias_criticas),
    }
    return render(request, 'estagio/monitoramento_pendencias.html', context)


@login_required
def api_monitoramento_pendencias(request):
    """
    API para atualização automática do monitoramento de pendências.
    
    CA4 - Exibição de pendências por tipo
    CA5 - Destaque para pendências críticas
    CA6 - Resultados consolidados
    """
    usuario = request.user
    
    # CA4 - Pendências por tipo
    pendencias = _obter_pendencias_por_perfil(usuario)
    pendencias_por_tipo = _agrupar_pendencias_por_tipo(pendencias)
    
    # CA5 - Pendências críticas
    pendencias_criticas = _filtrar_pendencias_criticas(pendencias)
    
    # CA6 - Resultados consolidados
    resultados_consolidados = _consolidar_resultados(usuario)
    
    dados = {
        'timestamp': timezone.now().isoformat(),
        'total_pendencias': len(pendencias),
        'total_criticas': len(pendencias_criticas),
        'pendencias_por_tipo': {
            tipo: {
                'quantidade': len(lista),
                'critico': TIPOS_PENDENCIA.get(tipo, {}).get('critico', False),
                'nome': TIPOS_PENDENCIA.get(tipo, {}).get('nome', tipo),
            }
            for tipo, lista in pendencias_por_tipo.items()
        },
        'pendencias_criticas': pendencias_criticas[:10],  # Limita a 10 mais recentes
        'resultados_consolidados': resultados_consolidados,
    }
    
    return JsonResponse(dados)


@login_required
def api_pendencias_por_tipo(request, tipo):
    """
    API para obter pendências filtradas por tipo específico.
    
    CA4 - O sistema deve permitir a exibição de pendências por tipo
    """
    usuario = request.user
    
    # Valida tipo
    if tipo not in TIPOS_PENDENCIA:
        return JsonResponse({'error': 'Tipo de pendência inválido'}, status=400)
    
    # Obtém pendências do tipo específico
    pendencias = _obter_pendencias_por_perfil(usuario)
    pendencias_filtradas = [p for p in pendencias if p['tipo'] == tipo]
    
    dados = {
        'tipo': tipo,
        'tipo_info': TIPOS_PENDENCIA[tipo],
        'quantidade': len(pendencias_filtradas),
        'pendencias': pendencias_filtradas,
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(dados)


@login_required
def api_resultados_consolidados(request):
    """
    API para obter resultados consolidados.
    
    CA6 - O sistema deve permitir a visualização de resultados consolidados
    """
    usuario = request.user
    
    resultados = _consolidar_resultados(usuario)
    resultados['timestamp'] = timezone.now().isoformat()
    
    return JsonResponse(resultados)


def _obter_pendencias_por_perfil(usuario):
    """
    Obtém todas as pendências conforme o perfil do usuário.
    Retorna lista de dicionários com informações das pendências.
    """
    pendencias = []
    
    if usuario.tipo == 'coordenador':
        pendencias.extend(_obter_pendencias_coordenador())
    elif usuario.tipo == 'supervisor':
        pendencias.extend(_obter_pendencias_supervisor(usuario))
    elif usuario.tipo == 'aluno':
        pendencias.extend(_obter_pendencias_aluno(usuario))
    
    # Ordena por criticidade (críticas primeiro) e depois por data
    pendencias.sort(key=lambda x: (not x['critico'], x.get('data', '')))
    
    return pendencias


def _obter_pendencias_coordenador():
    """Obtém pendências para o perfil de coordenador"""
    pendencias = []
    hoje = timezone.now().date()
    
    # Estágios em análise aguardando aprovação
    estagios_analise = Estagio.objects.filter(status='analise')
    for estagio in estagios_analise:
        pendencias.append({
            'tipo': 'estagio_analise',
            'titulo': f'Estágio "{estagio.titulo}" aguardando aprovação',
            'descricao': f'Solicitado por {estagio.aluno_solicitante.nome if estagio.aluno_solicitante else "N/A"}',
            'referencia_id': estagio.id,
            'referencia_tipo': 'estagio',
            'critico': False,
            'data': estagio.data_solicitacao.isoformat() if estagio.data_solicitacao else '',
        })
    
    # Documentos com prazo próximo (3 dias)
    prazo_limite = hoje + timedelta(days=3)
    documentos_prazo = Documento.objects.filter(
        prazo_limite__lte=prazo_limite,
        prazo_limite__gte=hoje,
        status__in=['enviado', 'ajustes_solicitados', 'corrigido']
    )
    for doc in documentos_prazo:
        dias_restantes = (doc.prazo_limite - hoje).days
        pendencias.append({
            'tipo': 'documento_prazo',
            'titulo': f'Documento "{doc.nome_arquivo}" com prazo em {dias_restantes} dia(s)',
            'descricao': f'Prazo: {doc.prazo_limite.strftime("%d/%m/%Y")}',
            'referencia_id': doc.id,
            'referencia_tipo': 'documento',
            'critico': True,
            'data': doc.prazo_limite.isoformat(),
        })
    
    return pendencias


def _obter_pendencias_supervisor(usuario):
    """Obtém pendências para o perfil de supervisor"""
    pendencias = []
    hoje = timezone.now().date()
    
    try:
        supervisor = Supervisor.objects.get(usuario=usuario)
    except Supervisor.DoesNotExist:
        return pendencias
    
    # Documentos aguardando análise do supervisor
    documentos_pendentes = Documento.objects.filter(
        supervisor=supervisor,
        status__in=['enviado', 'corrigido']
    )
    for doc in documentos_pendentes:
        pendencias.append({
            'tipo': 'documento_pendente',
            'titulo': f'Documento "{doc.nome_arquivo}" aguardando análise',
            'descricao': f'Enviado em {doc.data_envio.strftime("%d/%m/%Y")}',
            'referencia_id': doc.id,
            'referencia_tipo': 'documento',
            'critico': False,
            'data': doc.data_envio.isoformat(),
        })
    
    # Avaliações incompletas
    from estagio.models import Avaliacao
    avaliacoes_incompletas = Avaliacao.objects.filter(
        supervisor=supervisor,
        status__in=['rascunho', 'completa']
    )
    for avaliacao in avaliacoes_incompletas:
        if not avaliacao.is_completa():
            pendencias.append({
                'tipo': 'avaliacao_incompleta',
                'titulo': f'Avaliação de {avaliacao.aluno.nome if avaliacao.aluno else "N/A"} incompleta',
                'descricao': f'Período: {avaliacao.get_periodo_display()}',
                'referencia_id': avaliacao.id,
                'referencia_tipo': 'avaliacao',
                'critico': True,
                'data': avaliacao.created_at.isoformat() if avaliacao.created_at else '',
            })
    
    return pendencias


def _obter_pendencias_aluno(usuario):
    """Obtém pendências para o perfil de aluno"""
    pendencias = []
    hoje = timezone.now().date()
    
    try:
        aluno = Aluno.objects.get(usuario=usuario)
    except Aluno.DoesNotExist:
        return pendencias
    
    # Documentos com ajustes solicitados
    if aluno.estagio:
        documentos_ajuste = Documento.objects.filter(
            estagio=aluno.estagio,
            status='ajustes_solicitados'
        )
        for doc in documentos_ajuste:
            pendencias.append({
                'tipo': 'documento_ajuste',
                'titulo': f'Documento "{doc.nome_arquivo}" precisa de correção',
                'descricao': doc.observacoes_supervisor or 'Verifique as observações do supervisor',
                'referencia_id': doc.id,
                'referencia_tipo': 'documento',
                'critico': True,
                'data': doc.updated_at.isoformat() if doc.updated_at else '',
            })
        
        # Documentos com prazo próximo
        prazo_limite = hoje + timedelta(days=3)
        documentos_prazo = Documento.objects.filter(
            estagio=aluno.estagio,
            prazo_limite__lte=prazo_limite,
            prazo_limite__gte=hoje,
            status__in=['enviado', 'ajustes_solicitados']
        )
        for doc in documentos_prazo:
            dias_restantes = (doc.prazo_limite - hoje).days
            pendencias.append({
                'tipo': 'documento_prazo',
                'titulo': f'Documento "{doc.nome_arquivo}" vence em {dias_restantes} dia(s)',
                'descricao': f'Prazo: {doc.prazo_limite.strftime("%d/%m/%Y")}',
                'referencia_id': doc.id,
                'referencia_tipo': 'documento',
                'critico': True,
                'data': doc.prazo_limite.isoformat(),
            })
    
    return pendencias


def _agrupar_pendencias_por_tipo(pendencias):
    """
    CA4 - Agrupa pendências por tipo.
    """
    agrupadas = {}
    for pendencia in pendencias:
        tipo = pendencia['tipo']
        if tipo not in agrupadas:
            agrupadas[tipo] = []
        agrupadas[tipo].append(pendencia)
    return agrupadas


def _filtrar_pendencias_criticas(pendencias):
    """
    CA5 - Filtra apenas pendências críticas.
    """
    return [p for p in pendencias if p['critico']]


def _consolidar_resultados(usuario):
    """
    CA6 - Consolida resultados para exibição.
    
    Retorna estatísticas consolidadas de:
    - Estágios
    - Documentos
    - Avaliações
    - Horas cumpridas
    """
    from estagio.models import Avaliacao
    
    resultados = {
        'estagios': {},
        'documentos': {},
        'avaliacoes': {},
        'horas': {},
    }
    
    if usuario.tipo == 'coordenador':
        # Coordenador vê tudo
        estagios = Estagio.objects.all()
        documentos = Documento.objects.all()
        avaliacoes = Avaliacao.objects.all()
        horas = HorasCumpridas.objects.all()
        
    elif usuario.tipo == 'supervisor':
        try:
            supervisor = Supervisor.objects.get(usuario=usuario)
            estagios = Estagio.objects.filter(supervisor=supervisor)
            documentos = Documento.objects.filter(supervisor=supervisor)
            avaliacoes = Avaliacao.objects.filter(supervisor=supervisor)
            # Horas dos alunos dos estágios que supervisiona
            alunos_ids = estagios.values_list('aluno_solicitante_id', flat=True)
            horas = HorasCumpridas.objects.filter(aluno_id__in=alunos_ids)
        except Supervisor.DoesNotExist:
            estagios = Estagio.objects.none()
            documentos = Documento.objects.none()
            avaliacoes = Avaliacao.objects.none()
            horas = HorasCumpridas.objects.none()
            
    elif usuario.tipo == 'aluno':
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            estagios = Estagio.objects.filter(aluno_solicitante=aluno)
            documentos = Documento.objects.filter(estagio__aluno_solicitante=aluno)
            avaliacoes = Avaliacao.objects.filter(aluno=aluno)
            horas = HorasCumpridas.objects.filter(aluno=aluno)
        except Aluno.DoesNotExist:
            estagios = Estagio.objects.none()
            documentos = Documento.objects.none()
            avaliacoes = Avaliacao.objects.none()
            horas = HorasCumpridas.objects.none()
    else:
        estagios = Estagio.objects.none()
        documentos = Documento.objects.none()
        avaliacoes = Avaliacao.objects.none()
        horas = HorasCumpridas.objects.none()
    
    # Consolidação de estágios
    resultados['estagios'] = {
        'total': estagios.count(),
        'em_andamento': estagios.filter(status='em_andamento').count(),
        'aprovados': estagios.filter(status='aprovado').count(),
        'em_analise': estagios.filter(status='analise').count(),
        'reprovados': estagios.filter(status='reprovado').count(),
    }
    
    # Consolidação de documentos
    resultados['documentos'] = {
        'total': documentos.count(),
        'aprovados': documentos.filter(status='aprovado').count(),
        'pendentes': documentos.filter(status__in=['enviado', 'corrigido']).count(),
        'com_ajustes': documentos.filter(status='ajustes_solicitados').count(),
        'finalizados': documentos.filter(status='finalizado').count(),
    }
    
    # Consolidação de avaliações
    resultados['avaliacoes'] = {
        'total': avaliacoes.count(),
        'completas': avaliacoes.filter(status='parecer_emitido').count(),
        'em_andamento': avaliacoes.filter(status__in=['rascunho', 'completa', 'enviada']).count(),
        'nota_media': _calcular_nota_media_avaliacoes(avaliacoes),
    }
    
    # Consolidação de horas
    total_horas = horas.aggregate(total=Sum('quantidade'))['total'] or 0
    resultados['horas'] = {
        'total_registros': horas.count(),
        'total_horas': total_horas,
    }
    
    return resultados


def _calcular_nota_media_avaliacoes(avaliacoes):
    """Calcula a nota média das avaliações com parecer emitido"""
    avaliacoes_com_nota = avaliacoes.filter(
        status='parecer_emitido',
        nota_final__isnull=False
    )
    
    if not avaliacoes_com_nota.exists():
        return None
    
    from django.db.models import Avg
    media = avaliacoes_com_nota.aggregate(media=Avg('nota_final'))['media']
    return round(media, 2) if media else None


# =============================================================================
# Views de Geração de Relatórios de Estágios
# US: Geração de relatórios dos estágios
# CA1 - Filtros configuráveis
# CA2 - Dados completos do estágio
# CA3 - Validação de período
# =============================================================================

@login_required
def gerar_relatorio_estagios(request):
    """
    View principal para geração de relatórios de estágios.
    
    BDD: DADO que existem dados de estágios
         QUANDO o usuário solicitar um relatório
         ENTÃO o sistema deve gerar o relatório conforme filtros aplicados
    
    CA1 - Filtros configuráveis
    CA2 - Dados completos do estágio  
    CA3 - Validação de período
    """
    from .forms import RelatorioEstagiosForm
    from .models import Estagio, Documento, Avaliacao, HorasCumpridas, Aluno
    
    context = {
        'titulo': 'Geração de Relatórios de Estágios',
        'relatorio': None,
        'filtros_aplicados': {},
        'form': None,
    }
    
    if request.method == 'POST':
        form = RelatorioEstagiosForm(request.POST)
        
        if form.is_valid():
            # CA3 - Período validado pelo form
            relatorio = _gerar_relatorio_filtrado(request.user, form)
            context['relatorio'] = relatorio
            context['filtros_aplicados'] = form.get_filtros_ativos()
        else:
            context['erros'] = form.errors
    else:
        form = RelatorioEstagiosForm()
    
    context['form'] = form
    return render(request, 'estagio/gerar_relatorio.html', context)


@login_required
def api_relatorio_estagios(request):
    """
    API para geração de relatórios de estágios em formato JSON.
    
    CA1 - Aceita filtros configuráveis via query params ou POST
    CA2 - Retorna dados completos do estágio
    CA3 - Valida período informado
    """
    from .forms import RelatorioEstagiosForm
    
    # Aceita tanto GET quanto POST
    data = request.POST if request.method == 'POST' else request.GET
    form = RelatorioEstagiosForm(data)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors,
            'message': 'Erro na validação dos filtros'
        }, status=400)
    
    # CA1, CA2 - Gera relatório com filtros e dados completos
    relatorio = _gerar_relatorio_filtrado(request.user, form)
    
    return JsonResponse({
        'success': True,
        'filtros_aplicados': form.get_filtros_ativos(),
        'opcoes_inclusao': form.get_opcoes_inclusao(),
        'relatorio': relatorio,
        'total_estagios': len(relatorio.get('estagios', [])),
    })


@login_required  
def api_relatorio_exportar(request):
    """
    API para exportação de relatórios em diferentes formatos.
    
    CA1 - Exporta conforme filtros aplicados
    CA2 - Inclui todos os dados selecionados
    """
    from .forms import RelatorioEstagiosForm
    import csv
    from io import StringIO
    from django.http import HttpResponse
    
    data = request.POST if request.method == 'POST' else request.GET
    form = RelatorioEstagiosForm(data)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    relatorio = _gerar_relatorio_filtrado(request.user, form)
    formato = form.cleaned_data.get('formato', 'json')
    
    if formato == 'csv':
        return _exportar_csv(relatorio)
    else:
        return JsonResponse({
            'success': True,
            'relatorio': relatorio,
            'filtros': form.get_filtros_ativos(),
        })


def _gerar_relatorio_filtrado(usuario, form):
    """
    Gera o relatório de estágios aplicando os filtros do formulário.
    
    CA1 - Aplica filtros configuráveis
    CA2 - Inclui dados completos conforme seleção
    CA3 - Filtra por período quando informado
    
    Args:
        usuario: Usuário que está gerando o relatório
        form: RelatorioEstagiosForm validado
    
    Returns:
        dict: Relatório com estágios e dados relacionados
    """
    from .models import Estagio, Documento, Avaliacao, HorasCumpridas, Aluno
    from admin.models import CursoCoordenador, Supervisor
    
    # Base queryset conforme perfil do usuário
    estagios = _obter_estagios_por_perfil(usuario)
    
    # CA1, CA3 - Aplica filtros
    estagios = _aplicar_filtros_relatorio(estagios, form.cleaned_data)
    
    # CA2 - Opções de inclusão de dados
    opcoes = form.get_opcoes_inclusao()
    
    # Monta relatório com dados completos
    relatorio = {
        'estagios': [],
        'resumo': {
            'total': estagios.count(),
            'por_status': {},
            'por_empresa': {},
        },
        'periodo': form.get_filtros_ativos().get('periodo'),
        'data_geracao': timezone.now().isoformat(),
    }
    
    # Contabiliza por status
    for status_code, status_nome in Estagio.STATUS_CHOICES:
        count = estagios.filter(status=status_code).count()
        if count > 0:
            relatorio['resumo']['por_status'][status_nome] = count
    
    # CA2 - Monta dados completos de cada estágio
    for estagio in estagios.select_related('empresa', 'supervisor'):
        dados_estagio = _montar_dados_estagio(estagio, opcoes)
        relatorio['estagios'].append(dados_estagio)
        
        # Contabiliza por empresa
        empresa_nome = estagio.empresa.razao_social
        if empresa_nome not in relatorio['resumo']['por_empresa']:
            relatorio['resumo']['por_empresa'][empresa_nome] = 0
        relatorio['resumo']['por_empresa'][empresa_nome] += 1
    
    return relatorio


def _obter_estagios_por_perfil(usuario):
    """
    Retorna queryset de estágios conforme perfil do usuário.
    
    - Coordenador: Todos os estágios da instituição
    - Supervisor: Estágios sob sua supervisão
    - Aluno: Seus próprios estágios
    """
    from .models import Estagio, Aluno
    from admin.models import CursoCoordenador, Supervisor
    
    if usuario.tipo == 'coordenador':
        try:
            coordenador = CursoCoordenador.objects.get(usuario=usuario)
            alunos_instituicao = Aluno.objects.filter(
                instituicao=coordenador.instituicao
            ).values_list('id', flat=True)
            return Estagio.objects.filter(
                aluno_solicitante_id__in=alunos_instituicao
            )
        except CursoCoordenador.DoesNotExist:
            return Estagio.objects.all()
    
    elif usuario.tipo == 'supervisor':
        try:
            supervisor = Supervisor.objects.get(usuario=usuario)
            return Estagio.objects.filter(supervisor=supervisor)
        except Supervisor.DoesNotExist:
            return Estagio.objects.none()
    
    elif usuario.tipo == 'aluno':
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            return Estagio.objects.filter(aluno_solicitante=aluno)
        except Aluno.DoesNotExist:
            return Estagio.objects.none()
    
    return Estagio.objects.none()


def _aplicar_filtros_relatorio(estagios, filtros):
    """
    Aplica os filtros ao queryset de estágios.
    
    CA1 - Filtros configuráveis
    CA3 - Filtro de período
    """
    # CA3 - Filtro de período
    data_inicio = filtros.get('data_inicio')
    data_fim = filtros.get('data_fim')
    
    if data_inicio and data_fim:
        estagios = estagios.filter(
            data_inicio__gte=data_inicio,
            data_inicio__lte=data_fim
        )
    
    # CA1 - Filtro de status
    status = filtros.get('status')
    if status:
        estagios = estagios.filter(status=status)
    
    # CA1 - Filtro de empresa
    empresa = filtros.get('empresa')
    if empresa:
        estagios = estagios.filter(empresa=empresa)
    
    # CA1 - Filtro de supervisor
    supervisor = filtros.get('supervisor')
    if supervisor:
        estagios = estagios.filter(supervisor=supervisor)
    
    # CA1 - Filtro de instituição (via aluno)
    instituicao = filtros.get('instituicao')
    if instituicao:
        from .models import Aluno
        alunos_instituicao = Aluno.objects.filter(
            instituicao=instituicao
        ).values_list('id', flat=True)
        estagios = estagios.filter(aluno_solicitante_id__in=alunos_instituicao)
    
    return estagios


def _montar_dados_estagio(estagio, opcoes):
    """
    Monta dados completos de um estágio para o relatório.
    
    CA2 - Inclusão de dados completos do estágio
    """
    from .models import Documento, Avaliacao, HorasCumpridas
    
    dados = {
        'id': estagio.id,
        'titulo': estagio.titulo,
        'cargo': estagio.cargo,
        'status': estagio.status,
        'status_display': estagio.get_status_display(),
        'data_inicio': estagio.data_inicio.isoformat() if estagio.data_inicio else None,
        'data_fim': estagio.data_fim.isoformat() if estagio.data_fim else None,
        'carga_horaria': estagio.carga_horaria,
        'empresa': {
            'razao_social': estagio.empresa.razao_social,
            'cnpj': estagio.empresa.cnpj,
        },
        'supervisor': {
            'nome': estagio.supervisor.nome,
            'cargo': estagio.supervisor.cargo,
        },
    }
    
    # CA2 - Incluir dados do aluno
    if opcoes.get('aluno') and estagio.aluno_solicitante:
        dados['aluno'] = {
            'nome': estagio.aluno_solicitante.nome,
            'matricula': estagio.aluno_solicitante.matricula,
            'contato': estagio.aluno_solicitante.contato,
            'instituicao': estagio.aluno_solicitante.instituicao.nome if estagio.aluno_solicitante.instituicao else None,
        }
    
    # CA2 - Incluir documentos
    if opcoes.get('documentos'):
        documentos = Documento.objects.filter(estagio=estagio)
        dados['documentos'] = {
            'total': documentos.count(),
            'aprovados': documentos.filter(status='aprovado').count(),
            'pendentes': documentos.filter(status__in=['enviado', 'corrigido']).count(),
            'lista': [
                {
                    'id': doc.id,
                    'nome': doc.nome_arquivo,
                    'tipo': doc.tipo,
                    'status': doc.status,
                    'data_envio': doc.data_envio.isoformat() if doc.data_envio else None,
                }
                for doc in documentos[:10]  # Limita a 10 documentos
            ]
        }
    
    # CA2 - Incluir avaliações
    if opcoes.get('avaliacoes'):
        avaliacoes = Avaliacao.objects.filter(estagio=estagio)
        dados['avaliacoes'] = {
            'total': avaliacoes.count(),
            'completas': avaliacoes.filter(status='parecer_emitido').count(),
            'nota_media': _calcular_nota_media_avaliacoes(avaliacoes),
            'lista': [
                {
                    'id': av.id,
                    'periodo': av.get_periodo_display(),
                    'status': av.status,
                    'nota_final': av.nota_final,
                    'data_avaliacao': av.data_avaliacao.isoformat() if av.data_avaliacao else None,
                }
                for av in avaliacoes[:10]  # Limita a 10 avaliações
            ]
        }
    
    # CA2 - Incluir horas cumpridas
    if opcoes.get('horas') and estagio.aluno_solicitante:
        horas = HorasCumpridas.objects.filter(aluno=estagio.aluno_solicitante)
        total_horas = horas.aggregate(total=Sum('quantidade'))['total'] or 0
        dados['horas'] = {
            'total_registros': horas.count(),
            'total_horas': total_horas,
            'carga_horaria_estagio': estagio.carga_horaria,
        }
    
    return dados


def _exportar_csv(relatorio):
    """
    Exporta o relatório em formato CSV.
    
    CA1 - Exportação conforme filtros
    """
    from django.http import HttpResponse
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorio_estagios.csv"'
    response.write('\ufeff')  # BOM para Excel reconhecer UTF-8
    
    writer = csv.writer(response)
    
    # Cabeçalho
    writer.writerow([
        'ID', 'Título', 'Cargo', 'Status', 'Data Início', 'Data Fim',
        'Carga Horária', 'Empresa', 'Supervisor', 'Aluno', 'Matrícula',
        'Total Documentos', 'Docs Aprovados', 'Total Avaliações', 'Nota Média'
    ])
    
    # Dados
    for estagio in relatorio.get('estagios', []):
        aluno_nome = estagio.get('aluno', {}).get('nome', '-')
        aluno_matricula = estagio.get('aluno', {}).get('matricula', '-')
        docs = estagio.get('documentos', {})
        avs = estagio.get('avaliacoes', {})
        
        writer.writerow([
            estagio.get('id'),
            estagio.get('titulo'),
            estagio.get('cargo'),
            estagio.get('status_display'),
            estagio.get('data_inicio'),
            estagio.get('data_fim'),
            estagio.get('carga_horaria'),
            estagio.get('empresa', {}).get('razao_social'),
            estagio.get('supervisor', {}).get('nome'),
            aluno_nome,
            aluno_matricula,
            docs.get('total', 0),
            docs.get('aprovados', 0),
            avs.get('total', 0),
            avs.get('nota_media', '-'),
        ])
    
    return response


def validar_periodo_relatorio(data_inicio, data_fim):
    """
    CA3 - Função auxiliar para validação de período.
    Pode ser usada em validações externas.
    
    Args:
        data_inicio: Data de início do período
        data_fim: Data de fim do período
    
    Returns:
        tuple: (is_valid, error_message)
    """
    from datetime import date, timedelta
    
    if not data_inicio and not data_fim:
        return (True, None)
    
    if data_inicio and not data_fim:
        return (False, 'Informe a data fim para completar o período.')
    
    if data_fim and not data_inicio:
        return (False, 'Informe a data início para completar o período.')
    
    if data_fim < data_inicio:
        return (False, 'A data fim não pode ser anterior à data início.')
    
    if (data_fim - data_inicio).days > 365:
        return (False, 'O período máximo permitido é de 1 ano (365 dias).')
    
    if data_fim > date.today():
        return (False, 'A data fim não pode ser uma data futura.')
    
    return (True, None)


# ==================== VIEWS DE VAGAS DISPONÍVEIS ====================
# Sprint 03 - TASK 22173 e 22174


@login_required
@aluno_required
def listar_vagas_disponiveis(request):
    """
    View para ALUNO listar vagas disponíveis para candidatura.
    O aluno pode ver vagas aprovadas e disponíveis e se candidatar.
    """
    # Buscar vagas aprovadas e disponíveis
    vagas = Estagio.objects.filter(
        status='aprovado',
        status_vaga='disponivel'
    ).select_related('empresa', 'supervisor').order_by('-data_inicio')
    
    # Filtros
    filtro_empresa = request.GET.get('empresa', '')
    if filtro_empresa:
        vagas = vagas.filter(empresa__razao_social__icontains=filtro_empresa)
    
    filtro_cargo = request.GET.get('cargo', '')
    if filtro_cargo:
        vagas = vagas.filter(cargo__icontains=filtro_cargo)
    
    # Verifica se o aluno já tem estágio ativo
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        tem_estagio_ativo = aluno.estagio is not None
        
        # Verifica se tem solicitação pendente
        solicitacao_pendente = Estagio.objects.filter(
            aluno_solicitante=aluno,
            status='analise'
        ).first()
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        tem_estagio_ativo = False
        solicitacao_pendente = None
    
    context = {
        'vagas': vagas,
        'filtro_empresa': filtro_empresa,
        'filtro_cargo': filtro_cargo,
        'tem_estagio_ativo': tem_estagio_ativo,
        'solicitacao_pendente': solicitacao_pendente,
    }
    return render(request, 'estagio/listar_vagas_disponiveis.html', context)


@login_required
def detalhe_vaga(request, estagio_id):
    """
    View para visualizar detalhes de uma vaga disponível.
    TASK 22173 - Parte do fluxo de listagem de vagas
    """
    vaga = get_object_or_404(Estagio, id=estagio_id)
    
    # Verifica se o aluno já tem estágio ou solicitação pendente
    tem_estagio_ativo = False
    solicitacao_pendente = None
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        tem_estagio_ativo = aluno.estagio is not None
        solicitacao_pendente = Estagio.objects.filter(
            aluno_solicitante=aluno,
            status='analise'
        ).first()
    except:
        pass
    
    context = {
        'vaga': vaga,
        'tem_estagio_ativo': tem_estagio_ativo,
        'solicitacao_pendente': solicitacao_pendente,
    }
    return render(request, 'estagio/detalhe_vaga.html', context)


@login_required
@aluno_required
def candidatar_vaga(request, estagio_id):
    """
    View para ALUNO se candidatar a uma vaga existente.
    O aluno envia o documento e a solicitação fica pendente de aprovação.
    """
    vaga = get_object_or_404(Estagio, id=estagio_id)
    
    # Verificar se a vaga está disponível
    if not vaga.is_disponivel():
        messages.error(request, 'Esta vaga não está mais disponível.')
        return redirect('listar_vagas_disponiveis')
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        messages.error(request, "Erro: Aluno não encontrado.")
        return redirect('listar_vagas_disponiveis')
    
    # Verificar se o aluno já tem estágio ativo
    if aluno.estagio is not None:
        messages.error(request, 'Você já está vinculado a um estágio.')
        return redirect('acompanhar_estagios')
    
    # Verificar se já tem solicitação pendente
    solicitacao_pendente = Estagio.objects.filter(
        aluno_solicitante=aluno,
        status='analise'
    ).first()
    
    if solicitacao_pendente:
        messages.warning(
            request, 
            f'Você já possui uma solicitação pendente para "{solicitacao_pendente.titulo}". '
            'Aguarde a análise do coordenador.'
        )
        return redirect('listar_vagas_disponiveis')
    
    if request.method == 'POST':
        documento_form = DocumentoForm(request.POST, request.FILES)
        
        if documento_form.is_valid():
            # Atualiza a vaga com o aluno solicitante
            vaga.aluno_solicitante = aluno
            vaga.status = 'analise'  # Muda para análise
            vaga.save()
            
            # Recupera o coordenador selecionado
            coordenador = documento_form.cleaned_data['coordenador']
            
            # Cria o documento
            documento = documento_form.save(commit=False)
            documento.data_envio = now().date()
            documento.estagio = vaga
            documento.supervisor = vaga.supervisor
            documento.coordenador = coordenador
            documento.versao = 1.0
            documento.tipo = 'termo_compromisso'
            documento.nome_arquivo = documento.arquivo.name if documento.arquivo else 'documento.pdf'
            documento.enviado_por = usuario
            documento.save()
            
            # Registrar no histórico
            DocumentoHistorico.objects.create(
                documento=documento,
                acao='enviado',
                usuario=usuario,
                observacoes=f"Candidatura do aluno {aluno.nome} para a vaga {vaga.titulo}"
            )
            
            # Notificar coordenador
            try:
                enviar_notificacao_email(
                    destinatario=coordenador.usuario.email,
                    assunto=f"Nova candidatura: {aluno.nome} para {vaga.titulo}",
                    mensagem=f"O aluno {aluno.nome} se candidatou à vaga '{vaga.titulo}' "
                             f"na empresa {vaga.empresa.razao_social}. Por favor, analise a solicitação."
                )
            except Exception as e:
                logger.error(f"Erro ao enviar notificação: {e}")
            
            messages.success(
                request, 
                f'Candidatura enviada com sucesso! Aguarde a análise do coordenador.'
            )
            return redirect('historico_solicitacoes')
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        documento_form = DocumentoForm()
    
    context = {
        'vaga': vaga,
        'documento_form': documento_form,
        'aluno': aluno,
    }
    return render(request, 'estagio/candidatar_vaga.html', context)


# ==================== VIEWS DE ATIVIDADES ====================
# Sprint 03 - TASK 22180, 22181, 22182


@login_required
@supervisor_required
def listar_atividades_pendentes(request):
    """
    View para listar atividades pendentes de confirmação.
    TASK 22180 - [FRONT] Criar listagem de atividades pendentes de confirmação
    
    CA1 - Lista todas as atividades pendentes para o supervisor
    """
    from estagio.models import Atividade
    
    usuario = Usuario.objects.get(id=request.user.id)
    supervisor = Supervisor.objects.get(usuario=usuario)
    
    # Buscar atividades pendentes dos estágios supervisionados
    atividades = Atividade.objects.filter(
        estagio__supervisor=supervisor,
        status='pendente'
    ).select_related('aluno', 'estagio').order_by('-data_realizacao')
    
    # Filtro por aluno
    filtro_aluno = request.GET.get('aluno', '')
    if filtro_aluno:
        atividades = atividades.filter(aluno__nome__icontains=filtro_aluno)
    
    # Estatísticas
    total_pendentes = atividades.count()
    total_confirmadas = Atividade.objects.filter(
        estagio__supervisor=supervisor,
        status='confirmada'
    ).count()
    total_rejeitadas = Atividade.objects.filter(
        estagio__supervisor=supervisor,
        status='rejeitada'
    ).count()
    
    context = {
        'atividades': atividades,
        'filtro_aluno': filtro_aluno,
        'total_pendentes': total_pendentes,
        'total_confirmadas': total_confirmadas,
        'total_rejeitadas': total_rejeitadas,
    }
    return render(request, 'estagio/listar_atividades_pendentes.html', context)


@login_required
@supervisor_required
def detalhe_atividade(request, atividade_id):
    """
    View para visualizar detalhes de uma atividade.
    """
    from estagio.models import Atividade
    
    atividade = get_object_or_404(
        Atividade.objects.select_related('aluno', 'estagio', 'confirmado_por'),
        id=atividade_id
    )
    
    # Buscar histórico
    historico = atividade.historico.all().order_by('-data_hora')
    
    context = {
        'atividade': atividade,
        'historico': historico,
    }
    return render(request, 'estagio/detalhe_atividade.html', context)


@login_required
@supervisor_required
@require_POST
def confirmar_atividade(request, atividade_id):
    """
    View para confirmar uma atividade realizada.
    TASK 22181 - [FRONT] Implementar ação de confirmar atividade realizada
    
    CA2 - Confirmação da atividade pelo supervisor
    CA5 - Registro no histórico
    """
    from estagio.models import Atividade
    
    atividade = get_object_or_404(Atividade, id=atividade_id)
    
    # Verificar se a atividade está pendente
    if atividade.status != 'pendente':
        messages.error(request, 'Esta atividade já foi processada.')
        return redirect('listar_atividades_pendentes')
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Confirmar atividade
        atividade.confirmar(supervisor)
        
        messages.success(
            request,
            f'Atividade "{atividade.titulo}" confirmada com sucesso!'
        )
    except Exception as e:
        logger.error(f"Erro ao confirmar atividade: {e}")
        messages.error(request, 'Ocorreu um erro ao confirmar a atividade.')
    
    return redirect('listar_atividades_pendentes')


@login_required
@supervisor_required
@require_POST
def rejeitar_atividade(request, atividade_id):
    """
    View para rejeitar uma atividade com justificativa.
    TASK 22182 - [FRONT] Implementar ação de rejeitar atividade com justificativa
    
    CA3 - Rejeição com justificativa obrigatória
    CA5 - Registro no histórico
    """
    from estagio.models import Atividade
    
    atividade = get_object_or_404(Atividade, id=atividade_id)
    
    # Verificar se a atividade está pendente
    if atividade.status != 'pendente':
        messages.error(request, 'Esta atividade já foi processada.')
        return redirect('listar_atividades_pendentes')
    
    # Obter justificativa
    justificativa = request.POST.get('justificativa', '').strip()
    
    if not justificativa:
        messages.error(request, 'A justificativa é obrigatória para rejeitar uma atividade.')
        return redirect('detalhe_atividade', atividade_id=atividade_id)
    
    if len(justificativa) < 10:
        messages.error(request, 'A justificativa deve ter pelo menos 10 caracteres.')
        return redirect('detalhe_atividade', atividade_id=atividade_id)
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Rejeitar atividade
        atividade.rejeitar(supervisor, justificativa)
        
        messages.success(
            request,
            f'Atividade "{atividade.titulo}" rejeitada com justificativa.'
        )
    except Exception as e:
        logger.error(f"Erro ao rejeitar atividade: {e}")
        messages.error(request, 'Ocorreu um erro ao rejeitar a atividade.')
    
    return redirect('listar_atividades_pendentes')


# ==================== VIEWS DE AVALIAÇÃO ====================
# Sprint 03 - TASK 22186, 22191, 22193


@login_required
@supervisor_required
def formulario_avaliacao(request, estagio_id):
    """
    View para criar/editar formulário de avaliação com critérios definidos.
    TASK 22186 - [FRONT] Criar formulário de avaliação com critérios definidos
    
    CA1 - Avaliação com critérios previamente definidos
    CA2 - Salvamento associado ao período correto
    """
    from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
    
    estagio = get_object_or_404(Estagio, id=estagio_id)
    
    usuario = Usuario.objects.get(id=request.user.id)
    supervisor = Supervisor.objects.get(usuario=usuario)
    
    # Verificar se o supervisor é responsável pelo estágio
    if estagio.supervisor != supervisor:
        messages.error(request, 'Você não tem permissão para avaliar este estágio.')
        return redirect('supervisor:documentos')
    
    # Buscar aluno do estágio
    aluno = Aluno.objects.filter(estagio=estagio).first()
    
    # Buscar critérios ativos
    criterios = CriterioAvaliacao.objects.filter(ativo=True).order_by('ordem', 'nome')
    
    if request.method == 'POST':
        # Processar dados do formulário
        periodo = request.POST.get('periodo', 'mensal')
        periodo_inicio = request.POST.get('periodo_inicio')
        periodo_fim = request.POST.get('periodo_fim')
        
        try:
            from django.utils.dateparse import parse_date
            
            periodo_inicio_date = parse_date(periodo_inicio)
            periodo_fim_date = parse_date(periodo_fim)
            
            if not periodo_inicio_date or not periodo_fim_date:
                raise ValueError("Datas inválidas")
            
            if periodo_fim_date < periodo_inicio_date:
                messages.error(request, 'A data fim deve ser posterior à data início.')
                raise ValueError("Período inválido")
            
            # Criar avaliação
            avaliacao = Avaliacao.objects.create(
                supervisor=supervisor,
                estagio=estagio,
                aluno=aluno,
                periodo=periodo,
                periodo_inicio=periodo_inicio_date,
                periodo_fim=periodo_fim_date,
                data_avaliacao=timezone.now().date(),
                status='rascunho'
            )
            
            # Processar notas dos critérios
            for criterio in criterios:
                nota_valor = request.POST.get(f'criterio_{criterio.id}')
                observacao = request.POST.get(f'obs_{criterio.id}', '')
                
                if nota_valor:
                    try:
                        nota_float = float(nota_valor)
                        NotaCriterio.objects.create(
                            avaliacao=avaliacao,
                            criterio=criterio,
                            nota=nota_float,
                            observacao=observacao
                        )
                    except (ValueError, TypeError):
                        pass
            
            # Verificar se está completa e atualizar status
            if avaliacao.is_completa():
                avaliacao.status = 'completa'
                avaliacao.nota = avaliacao.calcular_nota_media()
                avaliacao.save()
            
            messages.success(request, 'Avaliação salva com sucesso!')
            return redirect('emitir_parecer', avaliacao_id=avaliacao.id)
            
        except Exception as e:
            logger.error(f"Erro ao salvar avaliação: {e}")
            messages.error(request, f'Erro ao salvar avaliação: {str(e)}')
    
    context = {
        'estagio': estagio,
        'aluno': aluno,
        'criterios': criterios,
    }
    return render(request, 'estagio/formulario_avaliacao.html', context)


@login_required
@supervisor_required
def emitir_parecer(request, avaliacao_id):
    """
    View para emitir parecer final com campo obrigatório.
    TASK 22191 - [FRONT] Criar campo obrigatório para parecer textual
    
    CA4 - Geração automática da nota final
    CA5 - Parecer textual obrigatório
    """
    from estagio.models import Avaliacao
    
    avaliacao = get_object_or_404(
        Avaliacao.objects.select_related('estagio', 'aluno', 'supervisor'),
        id=avaliacao_id
    )
    
    usuario = Usuario.objects.get(id=request.user.id)
    supervisor = Supervisor.objects.get(usuario=usuario)
    
    # Verificar permissão
    if avaliacao.supervisor != supervisor:
        messages.error(request, 'Você não tem permissão para emitir parecer desta avaliação.')
        return redirect('supervisor:documentos')
    
    # Buscar notas dos critérios
    notas_criterios = avaliacao.notas_criterios.select_related('criterio').all()
    
    if request.method == 'POST':
        parecer_texto = request.POST.get('parecer_final', '').strip()
        disponibilizar = request.POST.get('disponibilizar_consulta') == 'on'
        
        try:
            # Emitir parecer (validação e cálculo de nota são feitos no model)
            nota_final, parecer_final = avaliacao.emitir_parecer_final(
                parecer_texto, 
                disponibilizar_consulta=disponibilizar
            )
            
            messages.success(
                request,
                f'Parecer emitido com sucesso! Nota final: {nota_final:.2f}'
            )
            return redirect('visualizar_avaliacao', avaliacao_id=avaliacao.id)
            
        except ValueError as e:
            messages.error(request, str(e))
    
    context = {
        'avaliacao': avaliacao,
        'notas_criterios': notas_criterios,
        'nota_calculada': avaliacao.calcular_nota_media(),
    }
    return render(request, 'estagio/emitir_parecer.html', context)


@login_required
@supervisor_required
def visualizar_avaliacao(request, avaliacao_id):
    """
    View para visualizar avaliação completa.
    """
    from estagio.models import Avaliacao
    
    avaliacao = get_object_or_404(
        Avaliacao.objects.select_related('estagio', 'aluno', 'supervisor'),
        id=avaliacao_id
    )
    
    notas_criterios = avaliacao.notas_criterios.select_related('criterio').all()
    
    context = {
        'avaliacao': avaliacao,
        'notas_criterios': notas_criterios,
    }
    return render(request, 'estagio/visualizar_avaliacao.html', context)

