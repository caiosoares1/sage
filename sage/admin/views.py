from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from estagio.models import Estagio, Documento, DocumentoHistorico
from .models import CursoCoordenador, Supervisor
from users.models import Usuario
from utils.email import enviar_notificacao_email
from utils.decorators import supervisor_required, coordenador_required


def registrar_historico(documento, acao, usuario, observacoes=None):
    """Função auxiliar para registrar ações no histórico de documentos"""
    DocumentoHistorico.objects.create(
        documento=documento,
        acao=acao,
        usuario=usuario,
        observacoes=observacoes
    )

@login_required
def aprovar_estagio(request, estagio_id):
    """View para aprovar um estágio"""
    estagio = get_object_or_404(Estagio, id=estagio_id)
    estagio.status = "aprovado"
    estagio.save()
    messages.success(request, f"Estágio '{estagio.titulo}' foi aprovado com sucesso!")
    enviar_notificacao_email(
        destinatario="email@gmail.com",
        assunto="Estágio Aprovado",
        mensagem=f"Seu estágio '{estagio.titulo}' foi aprovado com sucesso!"
    )
    return redirect("estagio_detalhe", estagio.id)






@login_required
def reprovar_estagio(request, estagio_id):
    """View para reprovar um estágio"""
    estagio = get_object_or_404(Estagio, id=estagio_id)
    estagio.status = "reprovado"
    estagio.save()
    messages.success(request, f"Estágio '{estagio.titulo}' foi reprovado!")
    enviar_notificacao_email(
        destinatario="email@gmail.com",
        assunto="Estágio Reprovado",
        mensagem=f"Seu estágio '{estagio.titulo}' foi reprovado com sucesso!"
    )
    return redirect("estagio_detalhe", estagio.id)



@login_required
def listar_solicitacoes_coordenador(request):
    """View para o coordenador visualizar todas as solicitações de estágio em análise"""
    # Redireciona para a view correta de aprovação de documentos
    return redirect('aprovar_documentos_coordenador')


@login_required
@supervisor_required
def aprovar_documentos_supervisor(request):
    """View para o supervisor visualizar e gerenciar documentos"""
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Filtros
        status_filtro = request.GET.get('status', '')
        tipo_filtro = request.GET.get('tipo', '')
        
        # Base query - documentos dos estágios supervisionados por este supervisor
        documentos = Documento.objects.filter(
            estagio__supervisor=supervisor
        ).select_related(
            'estagio__empresa',
            'estagio__supervisor',
            'aprovado_por'
        ).prefetch_related(
            'estagio__aluno_set__usuario'
        ).order_by('-created_at')
        
        # Aplicar filtros
        if status_filtro:
            documentos = documentos.filter(status=status_filtro)
        if tipo_filtro:
            documentos = documentos.filter(tipo=tipo_filtro)
        
        # Calcular estatísticas
        stats = {
            'pendentes': Documento.objects.filter(
                estagio__supervisor=supervisor,
                status__in=['enviado', 'corrigido']
            ).count(),
            'aprovados': Documento.objects.filter(
                estagio__supervisor=supervisor,
                status__in=['aprovado', 'finalizado']  # Contar aprovados e finalizados
            ).count(),
            'reprovados': Documento.objects.filter(
                estagio__supervisor=supervisor,
                status='reprovado'
            ).count(),
            'total': Documento.objects.filter(
                estagio__supervisor=supervisor
            ).count()
        }
        
        context = {
            'documentos': documentos,
            'supervisor': supervisor,
            'stats': stats
        }
        return render(request, "admin/aprovar_documentos.html", context)
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def avaliar_documento(request, documento_id):
    """View para aprovar/reprovar um documento"""
    if request.method != 'POST':
        return redirect('aprovar_documentos_supervisor')
    
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Busca o documento e verifica se pertence a um estágio supervisionado por este supervisor
        documento = get_object_or_404(
            Documento,
            id=documento_id,
            estagio__supervisor=supervisor
        )
        
        # Pega a ação e observações
        acao = request.POST.get('acao')
        observacoes = request.POST.get('observacoes', '')
        
        # Capturar valores antes de modificar o documento
        tipo_documento = documento.tipo if documento.tipo else 'Documento'
        nome_arquivo = documento.nome_arquivo
        
        # Valida observações obrigatórias para reprovação e ajustes
        if acao in ['reprovar', 'solicitar_ajustes'] and not observacoes.strip():
            messages.error(request, "Observações são obrigatórias ao reprovar ou solicitar ajustes!")
            return redirect('aprovar_documentos_supervisor')
        
        # Atualiza o documento
        if acao == 'aprovar':
            documento.status = 'aprovado'
            registrar_historico(documento, 'aprovado', usuario, None)
            messages.success(request, f"Documento '{nome_arquivo}' aprovado com sucesso!")
        elif acao == 'reprovar':
            documento.status = 'reprovado'
            documento.observacoes_supervisor = observacoes
            registrar_historico(documento, 'reprovado', usuario, observacoes)
            messages.warning(request, f"Documento '{nome_arquivo}' reprovado.")
        elif acao == 'solicitar_ajustes':
            documento.status = 'ajustes_solicitados'
            documento.observacoes_supervisor = observacoes
            registrar_historico(documento, 'ajustes_solicitados', usuario, observacoes)
            messages.info(request, f"Ajustes solicitados para o documento '{nome_arquivo}'.")
        
        # Capturar status display após a modificação
        status_display = documento.get_status_display()
        
        documento.aprovado_por = usuario
        from django.utils import timezone
        documento.data_aprovacao = timezone.now()
        documento.save()
        
        # Enviar notificação ao aluno
        aluno = documento.estagio.aluno_set.first()
        if aluno:
            aluno_email = aluno.usuario.email
            enviar_notificacao_email(
                destinatario=aluno_email,
                assunto=f"Documento {tipo_documento} - {status_display}",
                mensagem=f"Seu documento '{nome_arquivo}' foi {status_display.lower()}.\n\n{observacoes if observacoes else ''}"
            )
        
        return redirect('supervisor:documentos')
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def visualizar_documento_supervisor(request, documento_id):
    """View para visualizar um documento específico"""
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Busca o documento e verifica permissão
        documento = get_object_or_404(
            Documento.objects.select_related(
                'estagio__empresa',
                'estagio__supervisor',
                'aprovado_por'
            ).prefetch_related(
                'estagio__aluno_set__usuario'
            ),
            id=documento_id,
            estagio__supervisor=supervisor
        )
        
        context = {
            'documento': documento,
            'supervisor': supervisor
        }
        return render(request, "admin/visualizar_documento.html", context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@coordenador_required
def aprovar_documentos_coordenador(request):
    """View para o coordenador visualizar e aprovar documentos já validados pelo supervisor"""
    try:
        # Busca o usuário e o coordenador vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        coordenador = CursoCoordenador.objects.get(usuario=usuario)
        
        # Filtros
        status_filtro = request.GET.get('status', '')
        tipo_filtro = request.GET.get('tipo', '')
        
        # Base query - todos os documentos do coordenador
        documentos = Documento.objects.filter(
            coordenador=coordenador
        ).select_related(
            'estagio__empresa',
            'estagio__supervisor',
            'aprovado_por'
        ).prefetch_related(
            'estagio__aluno_set__usuario'
        ).order_by('-created_at')
        
        # Aplicar filtro de status (padrão: apenas aprovados aguardando aprovação final)
        if status_filtro:
            documentos = documentos.filter(status=status_filtro)
        else:
            # Se não houver filtro, mostrar apenas os que aguardam aprovação
            documentos = documentos.filter(status='aprovado')
        
        # Aplicar filtro de tipo
        if tipo_filtro:
            documentos = documentos.filter(tipo=tipo_filtro)
        
        # Calcular estatísticas
        stats = {
            'aguardando': Documento.objects.filter(
                coordenador=coordenador,
                status='aprovado'  # Aprovados pelo supervisor, aguardando coordenador
            ).count(),
            'finalizados': Documento.objects.filter(
                coordenador=coordenador,
                status='finalizado'
            ).count(),
            'total': Documento.objects.filter(
                coordenador=coordenador
            ).count()
        }
        
        context = {
            'documentos': documentos,
            'coordenador': coordenador,
            'stats': stats
        }
        return render(request, "admin/aprovar_documentos_coordenador.html", context)
    except (Usuario.DoesNotExist, CursoCoordenador.DoesNotExist):
        messages.error(request, "Coordenador não encontrado!")
        return redirect('dashboard')


@login_required
@coordenador_required
def aprovar_documento_coordenador(request, documento_id):
    """View para coordenador aprovar um documento já validado pelo supervisor"""
    if request.method != 'POST':
        return redirect('aprovar_documentos_coordenador')
    
    try:
        # Busca o usuário e o coordenador vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        coordenador = CursoCoordenador.objects.get(usuario=usuario)
        
        # Busca o documento e verifica se pertence a este coordenador e está aprovado pelo supervisor
        documento = get_object_or_404(
            Documento,
            id=documento_id,
            coordenador=coordenador,
            status='aprovado'  # Deve estar aprovado pelo supervisor
        )
        
        # Capturar valores antes de modificar o documento
        tipo_documento = documento.tipo if documento.tipo else 'Documento'
        nome_arquivo = documento.nome_arquivo
        supervisor_nome = documento.estagio.supervisor.nome
        
        # Atualiza para finalizado
        documento.status = 'finalizado'
        from django.utils import timezone
        if not documento.data_aprovacao:
            documento.data_aprovacao = timezone.now()
        
        documento.save()
        
        # Atualizar status do estágio para 'em_andamento'
        estagio = documento.estagio
        if estagio.status == 'analise':
            estagio.status = 'em_andamento'
            estagio.save()
        
        # Registrar no histórico
        registrar_historico(documento, 'finalizado', usuario, "Aprovação final do coordenador")
        
        messages.success(request, f"Documento '{nome_arquivo}' aprovado com sucesso!")
        
        # Enviar notificação ao aluno
        aluno = documento.estagio.aluno_set.first()
        if aluno:
            aluno_email = aluno.usuario.email
            enviar_notificacao_email(
                destinatario=aluno_email,
                assunto=f"Documento {tipo_documento} - Aprovação Final",
                mensagem=f"Seu documento '{nome_arquivo}' foi aprovado pelo coordenador e está finalizado!"
            )
        
        # Enviar notificação ao supervisor
        supervisor_email = documento.estagio.supervisor.usuario.email
        enviar_notificacao_email(
            destinatario=supervisor_email,
            assunto=f"Documento {tipo_documento} - Aprovação Final",
            mensagem=f"O documento '{nome_arquivo}' foi aprovado pelo coordenador."
        )
        
        return redirect('coordenador:documentos')
        
    except (Usuario.DoesNotExist, CursoCoordenador.DoesNotExist):
        messages.error(request, "Coordenador não encontrado!")
        return redirect('dashboard')





