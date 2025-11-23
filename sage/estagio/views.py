from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib import messages
from admin.models import CursoCoordenador
from .forms import EstagioForm, DocumentoForm
from .models import Estagio
from users.models import Usuario
from estagio.models import Aluno


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

            messages.success(request, "Solicitação de estágio enviada com sucesso!")
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











