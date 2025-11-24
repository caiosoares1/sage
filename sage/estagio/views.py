from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib import messages
from admin.models import CursoCoordenador,Supervisor
from .forms import EstagioForm, DocumentoForm
from .models import Estagio, Documento
from users.models import Usuario
from estagio.models import Aluno
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal, InvalidOperation
from utils.email import enviar_notificacao_email
from django.utils.dateparse import parse_date


@login_required
def solicitar_estagio(request):
    if request.method == "POST":
        estagio_form = EstagioForm(request.POST)
        documento_form = DocumentoForm(request.POST, request.FILES)

        # Valida os dois formulários
        if estagio_form.is_valid() and documento_form.is_valid():
            # Salva estágio com status inicial "Em análise"
            estagio = estagio_form.save(commit=False)
            estagio.status = "analise"
            estagio.save()

            # Vincula o estágio ao aluno logado
            try:
                usuario = Usuario.objects.get(id=request.user.id)
                aluno = Aluno.objects.get(usuario=usuario)
                aluno.estagio = estagio
                aluno.save()
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
            documento.save()

            enviar_notificacao_email(
             destinatario="email@gmail.com",
             assunto=f"Novo documento enviado pelo aluno {aluno.nome}",
             mensagem=f"O aluno {aluno.nome} enviou um novo documento para o estágio. Por favor, revise o documento."
)
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
def acompanhar_estagios(request):
    """View para listar as solicitações de estágio do aluno logado"""  
    try:
        # Busca o usuário logado
        usuario = Usuario.objects.get(id=request.user.id)
        # Busca o aluno vinculado a este usuário
        aluno = Aluno.objects.get(usuario=usuario)
        
        # Como Aluno tem FK para Estagio, verificamos se existe estágio vinculado
        if aluno.estagio:
            estagios = [aluno.estagio]
        else:
            estagios = []
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        estagios = []
    
    return render(request, "estagio/acompanhar_estagios.html", {"estagios": estagios})


@login_required
def estagio_detalhe(request, estagio_id):
    """View para exibir detalhes de um estágio"""
    estagio = get_object_or_404(Estagio, id=estagio_id)
    return render(request, "estagio/estagio_detalhe.html", {"estagio": estagio})


@login_required
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
        if doc.enviado_por and getattr(doc.enviado_por, 'email', None):
            recipient = doc.enviado_por.email
        elif hasattr(doc, 'estagio'):
            # tentar obter um aluno vinculado ao estágio
            try:
                aluno = Aluno.objects.get(estagio=doc.estagio)
                if aluno and aluno.usuario and getattr(aluno.usuario, 'email', None):
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
        if doc.enviado_por and getattr(doc.enviado_por, 'email', None):
            recipient_email = doc.enviado_por.email
        else:
            try:
                aluno = Aluno.objects.get(estagio=doc.estagio)
                if aluno and aluno.usuario and getattr(aluno.usuario, 'email', None):
                    recipient_email = aluno.usuario.email
            except Exception:
                recipient_email = None

        if recipient_email:
            enviar_notificacao_email(
                destinatario=recipient_email,
                assunto=f"Documento aprovado: {doc.nome_arquivo}",
                mensagem=(
                    f"Seu documento '{doc.nome_arquivo}' foi aprovado pelo supervisor {supervisor_obj.nome}.\n\n"
                    "Acesse o sistema para mais informações."
                ),
            )

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
        if doc.enviado_por and getattr(doc.enviado_por, 'email', None):
            recipient_email = doc.enviado_por.email
        else:
            try:
                aluno = Aluno.objects.get(estagio=doc.estagio)
                if aluno and aluno.usuario and getattr(aluno.usuario, 'email', None):
                    recipient_email = aluno.usuario.email
            except Exception:
                recipient_email = None

        if recipient_email:
            mensagem = f"Seu documento '{doc.nome_arquivo}' foi reprovado pelo supervisor {supervisor_obj.nome}.\n\n"
            if observacoes:
                mensagem += f"Observações:\n{observacoes}\n\n"
            mensagem += "Por favor, acesse o sistema para mais detalhes."
            enviar_notificacao_email(destinatario=recipient_email, assunto=f"Documento reprovado: {doc.nome_arquivo}", mensagem=mensagem)

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
        if doc.enviado_por and getattr(doc.enviado_por, 'email', None):
            recipient = doc.enviado_por.email
        else:
            try:
                aluno = Aluno.objects.get(estagio=doc.estagio)
                if aluno and aluno.usuario and getattr(aluno.usuario, 'email', None):
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











