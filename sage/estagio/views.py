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
	"""
	Supervisor solicita ajustes em um documento.
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
		doc.status = 'ajustes_solicitados'
		if observacoes:
			doc.observacoes_supervisor = observacoes
		doc.save(update_fields=['status', 'observacoes_supervisor', 'updated_at'])
		return redirect("estagio_detalhe", estagio_id=doc.estagio.id)

	# GET: renderiza formulário simples para inserir observações
	return render(request, "estagio/supervisor_requerir_ajustes.html", {
		"documento": doc,
		"observacoes_iniciais": doc.observacoes_supervisor or ""
	})


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











