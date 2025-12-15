
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib import messages
from django.http import JsonResponse
from admin.models import CursoCoordenador,Supervisor
from .forms import EstagioForm, DocumentoForm, AlunoCadastroForm, HorasCumpridasForm, SupervisorAlunoSelectForm
from .models import Estagio, Documento, DocumentoHistorico, HorasCumpridas, Notificacao
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
import logging

@login_required
@aluno_required
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
            
            messages.success(request, "Documento enviado com sucesso! Sua solicitação está em análise.")
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
def estagio_detalhe(request, estagio_id):
    """View para exibir detalhes de um estágio"""
    estagio = get_object_or_404(Estagio, id=estagio_id)
    
    # Buscar documentos relacionados ao estágio
    documentos = Documento.objects.filter(
        estagio=estagio
    ).select_related('aprovado_por').order_by('-created_at')
    
    return render(request, "estagio/estagio_detalhe.html", {
        "estagio": estagio,
        "documentos": documentos
    })


@login_required
@aluno_required
def listar_documentos(request):
    """View para listar todos os documentos enviados pelo aluno"""
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        aluno = Aluno.objects.get(usuario=usuario)
        
        # Buscar todos os documentos relacionados aos estágios do aluno
        if aluno.estagio:
            documentos = Documento.objects.filter(
                estagio=aluno.estagio
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
        
        # Busca o histórico ordenado por data
        historico = documento.historico.select_related('usuario').order_by('-data_hora')
        
        # Busca versões do documento
        versoes = documento.get_history()
        
        context = {
            'documento': documento,
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
            if aluno and aluno.contato:
                recipient = aluno.contato
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
        try:
            aluno = Aluno.objects.get(estagio=doc.estagio)
            if aluno and aluno.contato:
                recipient_email = aluno.contato
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
        try:
            aluno = Aluno.objects.get(estagio=doc.estagio)
            if aluno and aluno.contato:
                recipient_email = aluno.contato
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
        try:
            aluno = Aluno.objects.get(estagio=doc.estagio)
            if aluno and aluno.contato:
                recipient = aluno.contato
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


@login_required
@aluno_required
def cadastrar_aluno(request):
    if request.method == 'POST':
        form = AlunoCadastroForm(request.POST)
        if form.is_valid():
            usuario = Usuario.objects.get(id=request.user.id)
            if Aluno.objects.filter(usuario=usuario).exists():
                messages.error(request, 'Você já possui um cadastro de aluno.')
                return redirect('cadastrar_aluno')
            aluno = form.save(commit=False)
            aluno.usuario = usuario
            aluno.save()
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = AlunoCadastroForm()
    return render(request, 'estagio/cadastrar_aluno.html', {'form': form})


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
        # Busca o aluno vinculado ao usuário para obter o email (contato)
        try:
            aluno = Aluno.objects.get(usuario=usuario)
            email_destinatario = aluno.contato
        except Aluno.DoesNotExist:
            # Se não for aluno, tenta buscar como supervisor ou coordenador
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
        data = {'count': 0, 'notificacoes': []}
    
    return JsonResponse(data)


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

