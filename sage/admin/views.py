from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import re
from estagio.models import Estagio, Documento, DocumentoHistorico, Notificacao
from .models import CursoCoordenador, Supervisor
from .forms import SupervisorForm, SupervisorEditForm
from users.models import Usuario
from utils.email import enviar_notificacao_email
from utils.decorators import supervisor_required, coordenador_required
import logging

logger = logging.getLogger(__name__)

# ==================== VIEWS DE EMPRESA ====================
# As views de Empresa foram migradas para a API REST.
# Use os endpoints em /api/empresas/ para gerenciar empresas.
# Veja admin/api_views.py e admin/serializers.py para detalhes.


# ==================== VIEWS DE SUPERVISOR ====================

@login_required
def listar_supervisores(request):
    """View para listar todos os supervisores cadastrados"""
    supervisores = Supervisor.objects.all().select_related('empresa', 'usuario').order_by('nome')
    
    # Filtro por nome
    filtro_nome = request.GET.get('nome', '')
    if filtro_nome:
        supervisores = supervisores.filter(nome__icontains=filtro_nome)
    
    # Filtro por empresa
    filtro_empresa = request.GET.get('empresa', '')
    if filtro_empresa:
        supervisores = supervisores.filter(empresa__razao_social__icontains=filtro_empresa)
    
    context = {
        'supervisores': supervisores,
        'filtro_nome': filtro_nome,
        'filtro_empresa': filtro_empresa,
    }
    return render(request, 'admin/listar_supervisores.html', context)


@login_required
def visualizar_supervisor(request, supervisor_id):
    """View para visualizar detalhes de um supervisor"""
    supervisor = get_object_or_404(
        Supervisor.objects.select_related('empresa', 'usuario'),
        id=supervisor_id
    )
    
    # Buscar estágios supervisionados
    estagios = Estagio.objects.filter(supervisor=supervisor)
    
    context = {
        'supervisor': supervisor,
        'estagios': estagios,
    }
    return render(request, 'admin/visualizar_supervisor.html', context)


@login_required
def cadastrar_supervisor(request):
    """
    View para cadastrar um novo supervisor vinculado a uma empresa.
    CA2 - Supervisor vinculado corretamente a uma empresa
    CA3 - Impede cadastro com dados obrigatórios ausentes (Nome, CNPJ, Cargo, Empresa)
    """
    if request.method == 'POST':
        form = SupervisorForm(request.POST)
        if form.is_valid():
            supervisor = form.save()
            messages.success(request, f"Supervisor '{supervisor.nome}' cadastrado com sucesso!")
            return redirect('visualizar_supervisor', supervisor_id=supervisor.id)
        else:
            # Adiciona erros do formulário como mensagens
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SupervisorForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin/cadastrar_supervisor.html', context)


@login_required
def editar_supervisor(request, supervisor_id):
    """
    View para editar um supervisor existente.
    CA3 - Impede cadastro com dados obrigatórios ausentes (Nome, Cargo, Empresa)
    """
    supervisor = get_object_or_404(
        Supervisor.objects.select_related('empresa', 'usuario'),
        id=supervisor_id
    )
    
    if request.method == 'POST':
        form = SupervisorEditForm(request.POST, instance=supervisor)
        if form.is_valid():
            supervisor = form.save()
            messages.success(request, f"Supervisor '{supervisor.nome}' atualizado com sucesso!")
            return redirect('visualizar_supervisor', supervisor_id=supervisor.id)
        else:
            # Adiciona erros do formulário como mensagens
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SupervisorEditForm(instance=supervisor)
    
    context = {
        'form': form,
        'supervisor': supervisor,
    }
    return render(request, 'admin/editar_supervisor.html', context)


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
            assunto = f"Documento {tipo_documento} - {status_display}"
            mensagem = f"Seu documento '{nome_arquivo}' foi {status_display.lower()}.\n\n{observacoes if observacoes else ''}"
            enviar_notificacao_email(
                destinatario=aluno_email,
                assunto=assunto,
                mensagem=mensagem
            )
            # Criar notificação no sistema
            try:
                Notificacao.objects.get_or_create(
                    destinatario=aluno_email,
                    assunto=assunto,
                    referencia=f"doc_{status_display.lower().replace(' ', '_')}_{documento.id}",
                    defaults={'mensagem': mensagem}
                )
            except Exception as e:
                logger.warning(f"Erro ao criar notificação: {str(e)}")
        
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
            assunto_aluno = f"Documento {tipo_documento} - Aprovação Final"
            mensagem_aluno = f"Seu documento '{nome_arquivo}' foi aprovado pelo coordenador e está finalizado!"
            enviar_notificacao_email(
                destinatario=aluno_email,
                assunto=assunto_aluno,
                mensagem=mensagem_aluno
            )
            # Criar notificação no sistema
            try:
                Notificacao.objects.get_or_create(
                    destinatario=aluno_email,
                    assunto=assunto_aluno,
                    referencia=f"doc_finalizado_{documento.id}",
                    defaults={'mensagem': mensagem_aluno}
                )
            except Exception as e:
                logger.warning(f"Erro ao criar notificação: {str(e)}")
        
        # Enviar notificação ao supervisor
        supervisor_email = documento.estagio.supervisor.usuario.email
        assunto_sup = f"Documento {tipo_documento} - Aprovação Final"
        mensagem_sup = f"O documento '{nome_arquivo}' foi aprovado pelo coordenador."
        enviar_notificacao_email(
            destinatario=supervisor_email,
            assunto=assunto_sup,
            mensagem=mensagem_sup
        )
        # Criar notificação no sistema
        try:
            Notificacao.objects.get_or_create(
                destinatario=supervisor_email,
                assunto=assunto_sup,
                referencia=f"doc_finalizado_{documento.id}",
                defaults={'mensagem': mensagem_sup}
            )
        except Exception as e:
            logger.warning(f"Erro ao criar notificação: {str(e)}")
        
        return redirect('coordenador:documentos')
        
    except (Usuario.DoesNotExist, CursoCoordenador.DoesNotExist):
        messages.error(request, "Coordenador não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def alterar_status_estagio(request, estagio_id):
    """View para o supervisor alterar o status do estágio para aprovado ou reprovado"""
    if request.method != 'POST':
        return redirect('supervisor:documentos')
    
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Busca o estágio e verifica se pertence a este supervisor
        estagio = get_object_or_404(
            Estagio,
            id=estagio_id,
            supervisor=supervisor
        )
        
        # Verifica se o estágio está em andamento (documento já foi finalizado)
        if estagio.status != 'em_andamento':
            messages.error(request, "O estágio precisa estar em andamento para alterar o status.")
            return redirect('supervisor:documentos')
        
        # Pega a ação
        acao = request.POST.get('acao')
        observacoes = request.POST.get('observacoes', '').strip()
        
        if acao == 'aprovar':
            estagio.status = 'aprovado'
            status_display = 'aprovado'
            messages.success(request, f"Estágio '{estagio.titulo}' foi aprovado com sucesso!")
        elif acao == 'reprovar':
            if not observacoes:
                messages.error(request, "Observações são obrigatórias para reprovar o estágio.")
                return redirect('supervisor:documentos')
            estagio.status = 'reprovado'
            status_display = 'reprovado'
            messages.success(request, f"Estágio '{estagio.titulo}' foi reprovado.")
        else:
            messages.error(request, "Ação inválida.")
            return redirect('supervisor:documentos')
        
        estagio.save()
        
        # Enviar notificação ao aluno
        aluno = estagio.aluno_set.first()
        if aluno:
            aluno_email = aluno.usuario.email
            mensagem = f"Seu estágio '{estagio.titulo}' foi {status_display}."
            if observacoes:
                mensagem += f"\n\nObservações: {observacoes}"
            enviar_notificacao_email(
                destinatario=aluno_email,
                assunto=f"Estágio {status_display.title()}",
                mensagem=mensagem
            )
        
        return redirect('supervisor:documentos')
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


# ==================== VIEWS DE ATIVIDADES (CONFIRMAÇÃO) ====================

@login_required
@supervisor_required
def listar_atividades_pendentes(request):
    """
    View para listar atividades pendentes de confirmação - CA1
    O supervisor visualiza todas as atividades dos estágios que ele supervisiona
    """
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Importa o modelo de Atividade
        from estagio.models import Atividade
        
        # Filtros
        status_filtro = request.GET.get('status', 'pendente')
        aluno_filtro = request.GET.get('aluno', '')
        
        # Base query - atividades dos estágios supervisionados por este supervisor
        atividades = Atividade.objects.filter(
            estagio__supervisor=supervisor
        ).select_related(
            'aluno__usuario',
            'estagio',
            'confirmado_por'
        ).order_by('-data_realizacao', '-data_registro')
        
        # Aplicar filtro de status
        if status_filtro:
            atividades = atividades.filter(status=status_filtro)
        
        # Aplicar filtro de aluno
        if aluno_filtro:
            atividades = atividades.filter(aluno__nome__icontains=aluno_filtro)
        
        # Calcular estatísticas
        stats = {
            'pendentes': Atividade.objects.filter(
                estagio__supervisor=supervisor,
                status='pendente'
            ).count(),
            'confirmadas': Atividade.objects.filter(
                estagio__supervisor=supervisor,
                status='confirmada'
            ).count(),
            'rejeitadas': Atividade.objects.filter(
                estagio__supervisor=supervisor,
                status='rejeitada'
            ).count(),
            'total': Atividade.objects.filter(
                estagio__supervisor=supervisor
            ).count()
        }
        
        context = {
            'atividades': atividades,
            'supervisor': supervisor,
            'stats': stats,
            'status_filtro': status_filtro,
            'aluno_filtro': aluno_filtro,
        }
        return render(request, 'admin/listar_atividades_pendentes.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def confirmar_atividade(request, atividade_id):
    """
    View para confirmar uma atividade realizada pelo aluno - CA2, CA4
    Registra a data de confirmação e atualiza o status automaticamente
    """
    if request.method != 'POST':
        return redirect('supervisor:atividades_pendentes')
    
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Importa o modelo de Atividade
        from estagio.models import Atividade
        
        # Busca a atividade e verifica se pertence a um estágio supervisionado por este supervisor
        atividade = get_object_or_404(
            Atividade,
            id=atividade_id,
            estagio__supervisor=supervisor,
            status='pendente'  # Só pode confirmar atividades pendentes
        )
        
        # CA2 e CA4 - Confirma a atividade com registro de data e atualização automática de status
        atividade.confirmar(supervisor)
        
        messages.success(request, f"Atividade '{atividade.titulo}' confirmada com sucesso!")
        
        # Envia notificação ao aluno
        aluno_email = atividade.aluno.usuario.email
        enviar_notificacao_email(
            destinatario=aluno_email,
            assunto="Atividade Confirmada",
            mensagem=f"Sua atividade '{atividade.titulo}' foi confirmada pelo supervisor."
        )
        
        # Cria notificação no sistema
        try:
            Notificacao.objects.get_or_create(
                destinatario=aluno_email,
                assunto="Atividade Confirmada",
                referencia=f"atividade_confirmada_{atividade.id}",
                defaults={
                    'mensagem': f"Sua atividade '{atividade.titulo}' foi confirmada pelo supervisor."
                }
            )
        except Exception as e:
            logger.warning(f"Erro ao criar notificação: {str(e)}")
        
        return redirect('supervisor:atividades_pendentes')
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def rejeitar_atividade(request, atividade_id):
    """
    View para rejeitar uma atividade com justificativa obrigatória - CA3, CA4
    Registra a justificativa e atualiza o status automaticamente
    """
    if request.method != 'POST':
        return redirect('supervisor:atividades_pendentes')
    
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Importa o modelo e formulário
        from estagio.models import Atividade
        from estagio.forms import RejeicaoAtividadeForm
        
        # Busca a atividade e verifica se pertence a um estágio supervisionado por este supervisor
        atividade = get_object_or_404(
            Atividade,
            id=atividade_id,
            estagio__supervisor=supervisor,
            status='pendente'  # Só pode rejeitar atividades pendentes
        )
        
        # Valida a justificativa usando o formulário
        form = RejeicaoAtividadeForm(request.POST)
        
        if not form.is_valid():
            # CA3 - Justificativa é obrigatória
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect('supervisor:atividades_pendentes')
        
        justificativa = form.cleaned_data['justificativa']
        
        # CA3 e CA4 - Rejeita a atividade com justificativa e atualização automática de status
        atividade.rejeitar(supervisor, justificativa)
        
        messages.warning(request, f"Atividade '{atividade.titulo}' foi rejeitada.")
        
        # Envia notificação ao aluno com a justificativa
        aluno_email = atividade.aluno.usuario.email
        enviar_notificacao_email(
            destinatario=aluno_email,
            assunto="Atividade Rejeitada",
            mensagem=f"Sua atividade '{atividade.titulo}' foi rejeitada.\n\nMotivo: {justificativa}"
        )
        
        # Cria notificação no sistema
        try:
            Notificacao.objects.get_or_create(
                destinatario=aluno_email,
                assunto="Atividade Rejeitada",
                referencia=f"atividade_rejeitada_{atividade.id}",
                defaults={
                    'mensagem': f"Sua atividade '{atividade.titulo}' foi rejeitada.\n\nMotivo: {justificativa}"
                }
            )
        except Exception as e:
            logger.warning(f"Erro ao criar notificação: {str(e)}")
        
        return redirect('supervisor:atividades_pendentes')
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def visualizar_atividade(request, atividade_id):
    """
    View para visualizar detalhes de uma atividade
    """
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Importa o modelo de Atividade
        from estagio.models import Atividade
        
        # Busca a atividade e verifica permissão
        atividade = get_object_or_404(
            Atividade.objects.select_related(
                'aluno__usuario',
                'estagio',
                'confirmado_por'
            ),
            id=atividade_id,
            estagio__supervisor=supervisor
        )
        
        context = {
            'atividade': atividade,
            'supervisor': supervisor,
        }
        return render(request, 'admin/visualizar_atividade.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def historico_atividade(request, atividade_id):
    """
    View para visualizar o histórico de confirmações/rejeições de uma atividade - CA5
    """
    try:
        # Busca o usuário e o supervisor vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Importa o modelo de Atividade
        from estagio.models import Atividade
        
        # Busca a atividade e verifica permissão
        atividade = get_object_or_404(
            Atividade.objects.select_related(
                'aluno__usuario',
                'estagio'
            ).prefetch_related(
                'historico__supervisor'
            ),
            id=atividade_id,
            estagio__supervisor=supervisor
        )
        
        # CA5 - Obtém o histórico de confirmações
        historico = atividade.historico.all()
        
        context = {
            'atividade': atividade,
            'historico': historico,
            'supervisor': supervisor,
        }
        return render(request, 'admin/historico_atividade.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


# ==================== VIEWS DE VÍNCULO ALUNO-VAGA ====================

@login_required
@coordenador_required
def listar_vagas_disponiveis(request):
    """
    View para listar vagas disponíveis para vínculo - CA4
    Exibe apenas vagas com status aprovado e status_vaga disponível
    """
    from estagio.models import Aluno
    
    # CA4 - Busca apenas vagas disponíveis
    vagas = Estagio.objects.filter(
        status='aprovado',
        status_vaga='disponivel'
    ).select_related('empresa', 'supervisor').order_by('titulo')
    
    # Filtro por empresa
    filtro_empresa = request.GET.get('empresa', '')
    if filtro_empresa:
        vagas = vagas.filter(empresa__razao_social__icontains=filtro_empresa)
    
    # Filtro por título
    filtro_titulo = request.GET.get('titulo', '')
    if filtro_titulo:
        vagas = vagas.filter(titulo__icontains=filtro_titulo)
    
    # Busca alunos sem vínculo para estatísticas
    alunos_disponiveis = Aluno.objects.filter(estagio__isnull=True).count()
    
    # Estatísticas
    stats = {
        'total_vagas': vagas.count(),
        'alunos_disponiveis': alunos_disponiveis,
    }
    
    context = {
        'vagas': vagas,
        'filtro_empresa': filtro_empresa,
        'filtro_titulo': filtro_titulo,
        'stats': stats,
    }
    return render(request, 'admin/listar_vagas_disponiveis.html', context)


@login_required
@coordenador_required
def vincular_aluno_vaga(request):
    """
    View para realizar o vínculo entre aluno e vaga - CA5, CA6, CA7, CA8
    """
    from estagio.forms import VinculoAlunoVagaForm
    from estagio.models import Aluno
    
    if request.method == 'POST':
        form = VinculoAlunoVagaForm(request.POST)
        
        if form.is_valid():
            aluno = form.cleaned_data['aluno']
            vaga = form.cleaned_data['vaga']
            observacoes = form.cleaned_data.get('observacoes', '')
            
            try:
                # CA5 - Verifica novamente se aluno já tem vaga ativa
                if aluno.estagio is not None:
                    messages.error(
                        request, 
                        f'O aluno {aluno.nome} já está vinculado a uma vaga ativa.'
                    )
                    return redirect('coordenador:vincular_aluno_vaga')
                
                # CA7 - Vincula o aluno à vaga (atualiza status_vaga automaticamente)
                # CA8 - Registra histórico (feito dentro do método)
                vaga.vincular_aluno(aluno, realizado_por=request.user)
                
                messages.success(
                    request,
                    f'Aluno {aluno.nome} vinculado com sucesso à vaga "{vaga.titulo}"!'
                )
                
                # Notifica o aluno por email
                try:
                    enviar_notificacao_email(
                        destinatario=aluno.contato,
                        assunto='Vínculo de Estágio Realizado',
                        mensagem=f'''
                        Olá {aluno.nome},
                        
                        Você foi vinculado(a) à vaga de estágio "{vaga.titulo}" na empresa {vaga.empresa.razao_social}.
                        
                        Detalhes da vaga:
                        - Cargo: {vaga.cargo}
                        - Carga horária: {vaga.carga_horaria}h/semana
                        - Início: {vaga.data_inicio.strftime("%d/%m/%Y")}
                        - Supervisor: {vaga.supervisor.nome}
                        
                        Atenciosamente,
                        Sistema SAGE
                        '''
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar notificação de vínculo: {e}")
                
                return redirect('coordenador:listar_vagas_disponiveis')
                
            except Exception as e:
                logger.error(f"Erro ao vincular aluno à vaga: {e}")
                messages.error(request, f'Erro ao realizar o vínculo: {str(e)}')
        else:
            # Adiciona erros do formulário como mensagens
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = VinculoAlunoVagaForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin/vincular_aluno_vaga.html', context)


@login_required
@coordenador_required
def desvincular_aluno_vaga(request, aluno_id):
    """
    View para desvincular um aluno de uma vaga - CA8
    """
    from estagio.models import Aluno
    
    aluno = get_object_or_404(Aluno.objects.select_related('estagio'), id=aluno_id)
    
    if aluno.estagio is None:
        messages.warning(request, f'O aluno {aluno.nome} não está vinculado a nenhuma vaga.')
        return redirect('coordenador:listar_vinculos')
    
    if request.method == 'POST':
        observacoes = request.POST.get('observacoes', '')
        vaga = aluno.estagio
        
        try:
            # CA8 - Registra histórico e desvincula
            vaga.desvincular_aluno(aluno, realizado_por=request.user, observacoes=observacoes)
            
            messages.success(
                request,
                f'Aluno {aluno.nome} desvinculado com sucesso da vaga "{vaga.titulo}"!'
            )
            
            return redirect('coordenador:listar_vinculos')
            
        except Exception as e:
            logger.error(f"Erro ao desvincular aluno: {e}")
            messages.error(request, f'Erro ao desvincular aluno: {str(e)}')
    
    context = {
        'aluno': aluno,
        'vaga': aluno.estagio,
    }
    return render(request, 'admin/desvincular_aluno_vaga.html', context)


@login_required
@coordenador_required
def listar_vinculos(request):
    """
    View para listar todos os vínculos ativos entre alunos e vagas
    """
    from estagio.models import Aluno
    
    # Busca alunos com vínculo ativo
    alunos_vinculados = Aluno.objects.filter(
        estagio__isnull=False
    ).select_related(
        'estagio__empresa',
        'estagio__supervisor',
        'usuario',
        'instituicao'
    ).order_by('nome')
    
    # Filtro por nome do aluno
    filtro_aluno = request.GET.get('aluno', '')
    if filtro_aluno:
        alunos_vinculados = alunos_vinculados.filter(nome__icontains=filtro_aluno)
    
    # Filtro por empresa
    filtro_empresa = request.GET.get('empresa', '')
    if filtro_empresa:
        alunos_vinculados = alunos_vinculados.filter(
            estagio__empresa__razao_social__icontains=filtro_empresa
        )
    
    # Estatísticas
    stats = {
        'total_vinculados': alunos_vinculados.count(),
        'alunos_sem_vinculo': Aluno.objects.filter(estagio__isnull=True).count(),
    }
    
    context = {
        'alunos_vinculados': alunos_vinculados,
        'filtro_aluno': filtro_aluno,
        'filtro_empresa': filtro_empresa,
        'stats': stats,
    }
    return render(request, 'admin/listar_vinculos.html', context)


@login_required
@coordenador_required
def historico_vinculo_aluno(request, aluno_id):
    """
    View para visualizar o histórico de vínculos de um aluno - CA8
    """
    from estagio.models import Aluno, VinculoHistorico
    
    aluno = get_object_or_404(
        Aluno.objects.select_related('usuario', 'instituicao', 'estagio'),
        id=aluno_id
    )
    
    # CA8 - Obtém o histórico de vínculos
    historico = VinculoHistorico.objects.filter(
        aluno=aluno
    ).select_related(
        'estagio__empresa',
        'realizado_por'
    ).order_by('-data_hora')
    
    context = {
        'aluno': aluno,
        'historico': historico,
    }
    return render(request, 'admin/historico_vinculo_aluno.html', context)


@login_required
@coordenador_required
def historico_vinculo_vaga(request, vaga_id):
    """
    View para visualizar o histórico de vínculos de uma vaga - CA8
    """
    from estagio.models import VinculoHistorico
    
    vaga = get_object_or_404(
        Estagio.objects.select_related('empresa', 'supervisor'),
        id=vaga_id
    )
    
    # CA8 - Obtém o histórico de vínculos da vaga
    historico = VinculoHistorico.objects.filter(
        estagio=vaga
    ).select_related(
        'aluno__usuario',
        'realizado_por'
    ).order_by('-data_hora')
    
    context = {
        'vaga': vaga,
        'historico': historico,
    }
    return render(request, 'admin/historico_vinculo_vaga.html', context)


# ==================== VIEWS DE AVALIAÇÃO DE DESEMPENHO ====================

@login_required
@supervisor_required
def listar_avaliacoes(request):
    """
    View para listar avaliações de desempenho do supervisor
    """
    from estagio.models import Avaliacao, Aluno
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Busca avaliações do supervisor
        avaliacoes = Avaliacao.objects.filter(
            supervisor=supervisor
        ).select_related(
            'estagio__empresa',
            'aluno'
        ).order_by('-data_avaliacao')
        
        # Filtro por status
        filtro_status = request.GET.get('status', '')
        if filtro_status:
            avaliacoes = avaliacoes.filter(status=filtro_status)
        
        # Filtro por aluno
        filtro_aluno = request.GET.get('aluno', '')
        if filtro_aluno:
            avaliacoes = avaliacoes.filter(aluno__nome__icontains=filtro_aluno)
        
        # Busca alunos supervisionados para nova avaliação
        alunos_supervisionados = Aluno.objects.filter(
            estagio__supervisor=supervisor,
            estagio__status='em_andamento'
        ).select_related('estagio')
        
        # Estatísticas
        stats = {
            'total': avaliacoes.count(),
            'rascunhos': avaliacoes.filter(status='rascunho').count(),
            'enviadas': avaliacoes.filter(status='enviada').count(),
        }
        
        context = {
            'avaliacoes': avaliacoes,
            'alunos_supervisionados': alunos_supervisionados,
            'filtro_status': filtro_status,
            'filtro_aluno': filtro_aluno,
            'stats': stats,
        }
        return render(request, 'admin/listar_avaliacoes.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def criar_avaliacao(request, aluno_id):
    """
    View para criar nova avaliação de desempenho - CA1, CA2
    """
    from estagio.models import Avaliacao, Aluno, CriterioAvaliacao, NotaCriterio
    from estagio.forms import AvaliacaoForm
    from datetime import date
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Busca o aluno e verifica se está vinculado ao supervisor
        aluno = get_object_or_404(
            Aluno.objects.select_related('estagio__supervisor'),
            id=aluno_id,
            estagio__supervisor=supervisor,
            estagio__status='em_andamento'
        )
        
        if request.method == 'POST':
            form = AvaliacaoForm(request.POST)
            
            if form.is_valid():
                avaliacao = form.save(commit=False)
                avaliacao.supervisor = supervisor
                avaliacao.estagio = aluno.estagio
                avaliacao.aluno = aluno
                avaliacao.data_avaliacao = date.today()
                avaliacao.status = 'rascunho'
                avaliacao.save()
                
                # Cria as notas de critérios vazias para preenchimento posterior
                criterios = CriterioAvaliacao.objects.filter(ativo=True)
                for criterio in criterios:
                    NotaCriterio.objects.create(
                        avaliacao=avaliacao,
                        criterio=criterio,
                        nota=None
                    )
                
                messages.success(
                    request,
                    f'Avaliação criada com sucesso! Preencha os critérios.'
                )
                return redirect('supervisor:editar_avaliacao', avaliacao_id=avaliacao.id)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        else:
            form = AvaliacaoForm()
        
        context = {
            'form': form,
            'aluno': aluno,
            'supervisor': supervisor,
        }
        return render(request, 'admin/criar_avaliacao.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def editar_avaliacao(request, avaliacao_id):
    """
    View para editar avaliação e preencher critérios - CA1, CA2, CA3
    """
    from estagio.models import Avaliacao, CriterioAvaliacao, NotaCriterio
    from estagio.forms import AvaliacaoForm, NotaCriterioForm
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        # Busca a avaliação
        avaliacao = get_object_or_404(
            Avaliacao.objects.select_related('aluno', 'estagio'),
            id=avaliacao_id,
            supervisor=supervisor
        )
        
        # Verifica se a avaliação pode ser editada
        if avaliacao.status == 'enviada':
            messages.warning(request, 'Esta avaliação já foi enviada e não pode ser editada.')
            return redirect('supervisor:visualizar_avaliacao', avaliacao_id=avaliacao.id)
        
        # Busca os critérios e notas existentes
        criterios = CriterioAvaliacao.objects.filter(ativo=True).order_by('ordem')
        notas_existentes = {nc.criterio_id: nc for nc in avaliacao.notas_criterios.all()}
        
        if request.method == 'POST':
            # Atualiza dados da avaliação
            form = AvaliacaoForm(request.POST, instance=avaliacao)
            
            erros = False
            
            if form.is_valid():
                form.save()
                
                # Processa as notas dos critérios
                for criterio in criterios:
                    nota_valor = request.POST.get(f'nota_{criterio.id}')
                    observacao = request.POST.get(f'observacao_{criterio.id}', '')
                    
                    # Converte nota para float ou None
                    try:
                        nota_float = float(nota_valor) if nota_valor else None
                    except ValueError:
                        nota_float = None
                    
                    # Valida nota
                    if nota_float is not None:
                        if nota_float < criterio.nota_minima or nota_float > criterio.nota_maxima:
                            messages.error(
                                request,
                                f'Nota do critério "{criterio.nome}" deve estar entre '
                                f'{criterio.nota_minima} e {criterio.nota_maxima}.'
                            )
                            erros = True
                            continue
                    
                    # CA3 - Valida critério obrigatório
                    if criterio.obrigatorio and nota_float is None:
                        messages.error(
                            request,
                            f'O critério "{criterio.nome}" é obrigatório.'
                        )
                        erros = True
                        continue
                    
                    # Atualiza ou cria a nota
                    if criterio.id in notas_existentes:
                        nota_criterio = notas_existentes[criterio.id]
                        nota_criterio.nota = nota_float
                        nota_criterio.observacao = observacao
                        nota_criterio.save()
                    else:
                        NotaCriterio.objects.create(
                            avaliacao=avaliacao,
                            criterio=criterio,
                            nota=nota_float,
                            observacao=observacao
                        )
                
                if not erros:
                    # Atualiza status se todos os critérios foram preenchidos
                    if avaliacao.is_completa():
                        avaliacao.status = 'completa'
                        avaliacao.nota = avaliacao.calcular_nota_media()
                        avaliacao.save()
                        messages.success(request, 'Avaliação salva e completa!')
                    else:
                        messages.success(request, 'Avaliação salva como rascunho.')
                    
                    return redirect('supervisor:editar_avaliacao', avaliacao_id=avaliacao.id)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        else:
            form = AvaliacaoForm(instance=avaliacao)
        
        # Prepara dados dos critérios com notas
        criterios_com_notas = []
        for criterio in criterios:
            nota_existente = notas_existentes.get(criterio.id)
            criterios_com_notas.append({
                'criterio': criterio,
                'nota': nota_existente.nota if nota_existente else None,
                'observacao': nota_existente.observacao if nota_existente else '',
            })
        
        # Verifica se está completa
        is_completa = avaliacao.is_completa()
        criterios_faltantes = avaliacao.get_criterios_faltantes() if not is_completa else []
        
        context = {
            'form': form,
            'avaliacao': avaliacao,
            'criterios_com_notas': criterios_com_notas,
            'is_completa': is_completa,
            'criterios_faltantes': criterios_faltantes,
            'supervisor': supervisor,
        }
        return render(request, 'admin/editar_avaliacao.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def enviar_avaliacao(request, avaliacao_id):
    """
    View para enviar avaliação completa - CA3
    Impede envio de avaliação incompleta
    """
    from estagio.models import Avaliacao
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        avaliacao = get_object_or_404(
            Avaliacao.objects.select_related('aluno', 'estagio'),
            id=avaliacao_id,
            supervisor=supervisor
        )
        
        # Verifica se já foi enviada
        if avaliacao.status == 'enviada':
            messages.warning(request, 'Esta avaliação já foi enviada.')
            return redirect('supervisor:listar_avaliacoes')
        
        if request.method == 'POST':
            # CA3 - Valida se está completa
            if not avaliacao.is_completa():
                criterios_faltantes = avaliacao.get_criterios_faltantes()
                nomes = ', '.join([c.nome for c in criterios_faltantes])
                messages.error(
                    request,
                    f'Não é possível enviar avaliação incompleta. Critérios faltantes: {nomes}'
                )
                return redirect('supervisor:editar_avaliacao', avaliacao_id=avaliacao.id)
            
            try:
                avaliacao.enviar()
                
                messages.success(
                    request,
                    f'Avaliação de {avaliacao.aluno.nome} enviada com sucesso! '
                    f'Nota final: {avaliacao.nota}'
                )
                
                # Notifica o aluno por email
                try:
                    enviar_notificacao_email(
                        destinatario=avaliacao.aluno.contato,
                        assunto='Nova Avaliação de Desempenho',
                        mensagem=f'''
                        Olá {avaliacao.aluno.nome},
                        
                        Uma nova avaliação de desempenho foi registrada para o seu estágio.
                        
                        Período: {avaliacao.periodo_inicio.strftime("%d/%m/%Y")} a {avaliacao.periodo_fim.strftime("%d/%m/%Y")}
                        Nota: {avaliacao.nota}
                        
                        Atenciosamente,
                        {supervisor.nome}
                        '''
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar notificação de avaliação: {e}")
                
                return redirect('supervisor:listar_avaliacoes')
                
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('supervisor:editar_avaliacao', avaliacao_id=avaliacao.id)
        
        # GET - Mostra confirmação
        context = {
            'avaliacao': avaliacao,
            'supervisor': supervisor,
        }
        return render(request, 'admin/enviar_avaliacao.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def visualizar_avaliacao(request, avaliacao_id):
    """
    View para visualizar detalhes de uma avaliação
    """
    from estagio.models import Avaliacao, CriterioAvaliacao
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        avaliacao = get_object_or_404(
            Avaliacao.objects.select_related('aluno', 'estagio__empresa').prefetch_related(
                'notas_criterios__criterio'
            ),
            id=avaliacao_id,
            supervisor=supervisor
        )
        
        context = {
            'avaliacao': avaliacao,
            'notas_criterios': avaliacao.notas_criterios.all().order_by('criterio__ordem'),
            'supervisor': supervisor,
        }
        return render(request, 'admin/visualizar_avaliacao.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def excluir_avaliacao(request, avaliacao_id):
    """
    View para excluir avaliação em rascunho
    """
    from estagio.models import Avaliacao
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        avaliacao = get_object_or_404(
            Avaliacao,
            id=avaliacao_id,
            supervisor=supervisor
        )
        
        # Só permite excluir rascunhos
        if avaliacao.status == 'enviada':
            messages.error(request, 'Não é possível excluir avaliação já enviada.')
            return redirect('supervisor:listar_avaliacoes')
        
        if request.method == 'POST':
            aluno_nome = avaliacao.aluno.nome
            avaliacao.delete()
            messages.success(request, f'Avaliação de {aluno_nome} excluída com sucesso!')
            return redirect('supervisor:listar_avaliacoes')
        
        context = {
            'avaliacao': avaliacao,
        }
        return render(request, 'admin/excluir_avaliacao.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


# ==================== VIEWS DE PARECER FINAL - CA4, CA5, CA6 ====================

@login_required
@supervisor_required
def emitir_parecer_final(request, avaliacao_id):
    """
    View para supervisor emitir o parecer final do estagiário.
    CA4 - Geração automática da nota final
    CA5 - Parecer textual obrigatório
    CA6 - Disponibilização para consulta
    
    BDD:
    DADO que a avaliação foi concluída
    QUANDO o supervisor emitir o parecer final
    ENTÃO o sistema deve gerar a nota e o parecer do estagiário
    """
    from estagio.models import Avaliacao
    from estagio.forms import ParecerFinalForm
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        avaliacao = get_object_or_404(
            Avaliacao.objects.select_related('aluno', 'estagio__empresa').prefetch_related(
                'notas_criterios__criterio'
            ),
            id=avaliacao_id,
            supervisor=supervisor
        )
        
        # Verifica se o parecer já foi emitido
        if avaliacao.status == 'parecer_emitido':
            messages.warning(request, 'O parecer final já foi emitido para esta avaliação.')
            return redirect('supervisor:visualizar_parecer', avaliacao_id=avaliacao.id)
        
        # Verifica se a avaliação está em estado válido
        if avaliacao.status not in ['completa', 'enviada']:
            messages.error(
                request, 
                'A avaliação deve estar completa ou enviada para emitir o parecer final.'
            )
            return redirect('supervisor:editar_avaliacao', avaliacao_id=avaliacao.id)
        
        # CA4 - Calcula preview da nota final
        nota_preview = avaliacao.calcular_nota_media()
        
        if request.method == 'POST':
            form = ParecerFinalForm(request.POST, avaliacao=avaliacao)
            
            if form.is_valid():
                try:
                    parecer_texto = form.cleaned_data['parecer_final']
                    disponibilizar = form.cleaned_data['disponibilizar_consulta']
                    
                    # Emite o parecer final (CA4, CA5, CA6)
                    nota_final, parecer_final = avaliacao.emitir_parecer_final(
                        parecer_texto=parecer_texto,
                        disponibilizar_consulta=disponibilizar
                    )
                    
                    messages.success(
                        request,
                        f'Parecer final emitido com sucesso! '
                        f'Nota final: {nota_final:.2f}'
                    )
                    
                    # Notifica o aluno por email se parecer disponibilizado
                    if disponibilizar:
                        try:
                            enviar_notificacao_email(
                                destinatario=avaliacao.aluno.contato,
                                assunto='Parecer Final de Avaliação Disponível',
                                mensagem=f'''
                                Olá {avaliacao.aluno.nome},
                                
                                O parecer final da sua avaliação de estágio foi emitido e está disponível para consulta.
                                
                                Período Avaliado: {avaliacao.periodo_inicio.strftime("%d/%m/%Y")} a {avaliacao.periodo_fim.strftime("%d/%m/%Y")}
                                Nota Final: {nota_final:.2f}
                                
                                Acesse o sistema para visualizar o parecer completo.
                                
                                Atenciosamente,
                                {supervisor.nome}
                                '''
                            )
                        except Exception as e:
                            logger.error(f"Erro ao enviar notificação de parecer: {e}")
                    
                    return redirect('supervisor:visualizar_parecer', avaliacao_id=avaliacao.id)
                    
                except ValueError as e:
                    messages.error(request, str(e))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        else:
            form = ParecerFinalForm(avaliacao=avaliacao)
        
        # Prepara dados dos critérios com notas
        notas_criterios = avaliacao.notas_criterios.all().order_by('criterio__ordem')
        
        context = {
            'form': form,
            'avaliacao': avaliacao,
            'nota_preview': nota_preview,
            'notas_criterios': notas_criterios,
            'supervisor': supervisor,
        }
        return render(request, 'admin/emitir_parecer_final.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def visualizar_parecer(request, avaliacao_id):
    """
    View para supervisor visualizar o parecer final emitido.
    CA6 - Disponibilização do parecer para consulta
    """
    from estagio.models import Avaliacao
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        avaliacao = get_object_or_404(
            Avaliacao.objects.select_related('aluno', 'estagio__empresa').prefetch_related(
                'notas_criterios__criterio'
            ),
            id=avaliacao_id,
            supervisor=supervisor
        )
        
        # Verifica se o parecer foi emitido
        if avaliacao.status != 'parecer_emitido':
            messages.warning(request, 'O parecer final ainda não foi emitido.')
            return redirect('supervisor:emitir_parecer_final', avaliacao_id=avaliacao.id)
        
        context = {
            'avaliacao': avaliacao,
            'notas_criterios': avaliacao.notas_criterios.all().order_by('criterio__ordem'),
            'supervisor': supervisor,
        }
        return render(request, 'admin/visualizar_parecer_final.html', context)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')


@login_required
@supervisor_required
def alternar_disponibilidade_parecer(request, avaliacao_id):
    """
    View para supervisor alternar disponibilidade do parecer para consulta.
    CA6 - Controle de disponibilização do parecer
    """
    from estagio.models import Avaliacao
    
    try:
        usuario = Usuario.objects.get(id=request.user.id)
        supervisor = Supervisor.objects.get(usuario=usuario)
        
        avaliacao = get_object_or_404(
            Avaliacao,
            id=avaliacao_id,
            supervisor=supervisor
        )
        
        if avaliacao.status != 'parecer_emitido':
            messages.error(request, 'O parecer deve ser emitido antes de alterar a disponibilidade.')
            return redirect('supervisor:listar_avaliacoes')
        
        if request.method == 'POST':
            try:
                nova_disponibilidade = not avaliacao.parecer_disponivel_consulta
                avaliacao.disponibilizar_parecer_consulta(nova_disponibilidade)
                
                if nova_disponibilidade:
                    messages.success(request, 'Parecer disponibilizado para consulta pelo aluno.')
                else:
                    messages.success(request, 'Parecer ocultado da consulta pelo aluno.')
                    
            except ValueError as e:
                messages.error(request, str(e))
        
        return redirect('supervisor:visualizar_parecer', avaliacao_id=avaliacao.id)
        
    except (Usuario.DoesNotExist, Supervisor.DoesNotExist):
        messages.error(request, "Supervisor não encontrado!")
        return redirect('dashboard')

