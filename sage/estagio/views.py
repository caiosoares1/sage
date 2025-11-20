from django.shortcuts import render, redirect
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

        # Valida os dois formulários (CA2)
        if estagio_form.is_valid() and documento_form.is_valid():

            # Salva estágio COM status inicial "Em análise" (CA3)
            estagio = estagio_form.save(commit=False)
            estagio.status = "analise"
            estagio.save()


             # Recupera o nome digitado no form
            coordenador_nome = documento_form.cleaned_data['coordenador_nome']

            # Busca no banco
            try:
                coordenador = CursoCoordenador.objects.get(nome=coordenador_nome)
            except CursoCoordenador.DoesNotExist:
                messages.error(request, "Coordenador não encontrado!")
                return render(request, "solicitar_estagio.html", {
                    "estagio_form": estagio_form,
                    "documento_form": documento_form
                })

            # Vincula o documento ao estágio (CA1)
            documento = documento_form.save(commit=False)
            documento.data_envio = now().date()
            documento.estagio = estagio
            documento.supervisor = estagio.supervisor
            documento.coordenador = coordenador
            documento.save()

            return redirect("estagio_detalhe", estagio.id)

    else:
        estagio_form = EstagioForm()
        documento_form = DocumentoForm()

    return render(request, "solicitar_estagio.html", {
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
        # Filtra os estágios do aluno
        estagios = Estagio.objects.filter(aluno=aluno)
    except (Usuario.DoesNotExist, Aluno.DoesNotExist):
        estagios = []
    
    return render(request, "acompanhar_estagios.html", {"estagios": estagios})











