from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from estagio.models import Estagio, Documento
from .models import CursoCoordenador
from users.models import Usuario


@login_required
def aprovar_estagio(request, estagio_id):
    """View para aprovar um estágio"""
    estagio = get_object_or_404(Estagio, id=estagio_id)
    estagio.status = "aprovado"
    estagio.save()
    messages.success(request, f"Estágio '{estagio.titulo}' foi aprovado com sucesso!")
    return redirect("estagio_detalhe", estagio.id)


@login_required
def reprovar_estagio(request, estagio_id):
    """View para reprovar um estágio"""
    estagio = get_object_or_404(Estagio, id=estagio_id)
    estagio.status = "reprovado"
    estagio.save()
    messages.success(request, f"Estágio '{estagio.titulo}' foi reprovado!")
    return redirect("estagio_detalhe", estagio.id)


@login_required
def listar_solicitacoes_coordenador(request):
    """View para o coordenador visualizar todas as solicitações de estágio em análise"""
    try:
        # Busca o usuário e o coordenador vinculado
        usuario = Usuario.objects.get(id=request.user.id)
        coordenador = CursoCoordenador.objects.get(usuario=usuario)
        
        # Filtra os documentos associados a este coordenador
        documentos = Documento.objects.filter(coordenador=coordenador).select_related('estagio')
        
        context = {
            'documentos': documentos,
            'coordenador': coordenador
        }
        return render(request, "admin/listar_solicitacoes_coordenador.html", context)
    except (Usuario.DoesNotExist, CursoCoordenador.DoesNotExist):
        messages.error(request, "Coordenador não encontrado!")
        return redirect('home')




