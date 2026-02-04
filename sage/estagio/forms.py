# Formulário para seleção/pesquisa de aluno para supervisor
import re
from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from estagio.models import Aluno
from .models import Estagio, Documento, Aluno, HorasCumpridas
from admin.models import CursoCoordenador

class EstagioForm(forms.ModelForm):
    class Meta:
        model = Estagio
        fields = [
            'titulo', 'cargo', 'empresa', 'supervisor',
            'data_inicio', 'data_fim', 'carga_horaria'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Estágio em Desenvolvimento Web',
                'maxlength': '30'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Desenvolvedor Junior',
                'maxlength': '50'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-control'
            }),
            'supervisor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_fim': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'carga_horaria': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 20',
                'min': '1',
                'max': '40'
            })
        }
        labels = {
            'titulo': 'Título do Estágio',
            'cargo': 'Cargo/Função',
            'empresa': 'Empresa',
            'supervisor': 'Supervisor',
            'data_inicio': 'Data de Início',
            'data_fim': 'Data de Término',
            'carga_horaria': 'Carga Horária (horas/semana)'
        }

    def clean_data_inicio(self):
        data_inicio = self.cleaned_data.get('data_inicio')
        if data_inicio and data_inicio < date.today():
            raise ValidationError('A data de início não pode ser anterior a hoje.')
        return data_inicio

    def clean_data_fim(self):
        data_fim = self.cleaned_data.get('data_fim')
        data_inicio = self.cleaned_data.get('data_inicio')
        
        if data_fim and data_inicio and data_fim <= data_inicio:
            raise ValidationError('A data de término deve ser posterior à data de início.')
        return data_fim

    def clean_carga_horaria(self):
        carga_horaria = self.cleaned_data.get('carga_horaria')
        if carga_horaria and (carga_horaria < 1 or carga_horaria > 40):
            raise ValidationError('A carga horária deve estar entre 1 e 40 horas por semana.')
        return carga_horaria


class DocumentoForm(forms.ModelForm):
    coordenador = forms.ModelChoiceField(
        queryset=CursoCoordenador.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Coordenador do Curso',
        empty_label='Selecione um coordenador'
    )

    class Meta:
        model = Documento
        fields = ['arquivo']
        widgets = {
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx'
            })
        }
        labels = {
            'arquivo': 'Termo de Compromisso (PDF ou DOCX)'
        }

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo:
            # Validar tamanho do arquivo (max 10MB)
            if arquivo.size > 10 * 1024 * 1024:
                raise ValidationError('O arquivo não pode ser maior que 10MB.')
            
            # Validar extensão (PDF ou DOCX)
            if not (arquivo.name.endswith('.pdf') or arquivo.name.endswith('.docx')):
                raise ValidationError('Apenas arquivos PDF ou DOCX são permitidos.')
        
        return arquivo

    def clean_coordenador(self):
        coordenador = self.cleaned_data.get('coordenador')
        if not coordenador:
            raise ValidationError('Selecione um coordenador.')
        return coordenador


class AlunoCadastroForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome', 'contato', 'matricula', 'instituicao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'contato': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matrícula'}),
            'instituicao': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        if not nome:
            raise forms.ValidationError('O campo Nome é obrigatório.')
        if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', nome):
            raise forms.ValidationError('O nome deve conter apenas letras.')
        return nome

    def clean_contato(self):
        contato = self.cleaned_data.get('contato', '')
        if not contato:
            raise forms.ValidationError('O campo E-mail é obrigatório.')
        # Django já valida formato de email
        return contato

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula', '')
        if not matricula:
            raise forms.ValidationError('O campo Matrícula é obrigatório.')
        if not matricula.isdigit():
            raise forms.ValidationError('A matrícula deve conter apenas números.')
        qs = Aluno.objects.filter(matricula=matricula)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Esta matrícula já está cadastrada.')
        return matricula

class HorasCumpridasForm(forms.ModelForm):
    class Meta:
        model = HorasCumpridas
        fields = ['data', 'quantidade', 'descricao']
        widgets = {
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição das atividades'})
        }

    def clean_data(self):
        data = self.cleaned_data.get('data')
        if not data:
            raise forms.ValidationError('O campo data é obrigatório.')
        from datetime import date as dtdate
        if data > dtdate.today():
            raise forms.ValidationError('Não é permitido cadastrar horas em data futura.')
        return data

    def clean_quantidade(self):
        quantidade = self.cleaned_data.get('quantidade')
        if quantidade is None:
            raise forms.ValidationError('O campo quantidade de horas é obrigatório.')
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise forms.ValidationError('A quantidade de horas deve ser numérica e maior que zero.')
        return quantidade

    def clean_descricao(self):
        descricao = self.cleaned_data.get('descricao', '').strip()
        if not descricao:
            raise forms.ValidationError('O campo descrição é obrigatório.')
        return descricao
    


class SupervisorAlunoSelectForm(forms.Form):
    aluno = forms.ModelChoiceField(queryset=None, label="Selecione o aluno", required=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['aluno'].queryset = Aluno.objects.select_related('usuario', 'instituicao').all()


class AtividadeForm(forms.ModelForm):
    """Formulário para registro de atividades pelo aluno"""
    
    class Meta:
        from .models import Atividade
        model = Atividade
        fields = ['titulo', 'descricao', 'data_realizacao', 'horas_dedicadas']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da atividade realizada',
                'maxlength': '200'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descreva detalhadamente a atividade realizada',
                'rows': 4
            }),
            'data_realizacao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'horas_dedicadas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Horas dedicadas'
            }),
        }
        labels = {
            'titulo': 'Título da Atividade',
            'descricao': 'Descrição',
            'data_realizacao': 'Data de Realização',
            'horas_dedicadas': 'Horas Dedicadas',
        }
        error_messages = {
            'titulo': {
                'required': 'Título é obrigatório.',
            },
            'descricao': {
                'required': 'Descrição é obrigatória.',
            },
            'data_realizacao': {
                'required': 'Data de realização é obrigatória.',
            },
            'horas_dedicadas': {
                'required': 'Horas dedicadas é obrigatório.',
            },
        }
    
    def clean_data_realizacao(self):
        data_realizacao = self.cleaned_data.get('data_realizacao')
        if data_realizacao and data_realizacao > date.today():
            raise ValidationError('A data de realização não pode ser futura.')
        return data_realizacao
    
    def clean_horas_dedicadas(self):
        horas = self.cleaned_data.get('horas_dedicadas')
        if horas is not None and horas <= 0:
            raise ValidationError('As horas dedicadas devem ser maiores que zero.')
        if horas is not None and horas > 24:
            raise ValidationError('As horas dedicadas não podem exceder 24 horas por dia.')
        return horas


class RejeicaoAtividadeForm(forms.Form):
    """Formulário para rejeição de atividade com justificativa obrigatória - CA3"""
    
    justificativa = forms.CharField(
        required=True,
        min_length=10,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Informe o motivo da rejeição (mínimo 10 caracteres)',
            'rows': 3
        }),
        label='Justificativa',
        error_messages={
            'required': 'Justificativa é obrigatória para rejeição.',
            'min_length': 'A justificativa deve ter pelo menos 10 caracteres.',
        }
    )
    
    def clean_justificativa(self):
        justificativa = self.cleaned_data.get('justificativa', '').strip()
        if not justificativa:
            raise ValidationError('Justificativa é obrigatória para rejeição.')
        if len(justificativa) < 10:
            raise ValidationError('A justificativa deve ter pelo menos 10 caracteres.')
        return justificativa


class VinculoAlunoVagaForm(forms.Form):
    """
    Formulário para vincular um aluno a uma vaga de estágio.
    CA4 - Exibe apenas vagas disponíveis
    CA5 - Valida que aluno só pode ter uma vaga ativa
    CA6 - Impede vínculo duplicado
    
    O parâmetro `instituicao` filtra os alunos pela instituição do coordenador.
    """
    
    aluno = forms.ModelChoiceField(
        queryset=Aluno.objects.none(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Aluno',
        empty_label='Selecione um aluno'
    )
    
    vaga = forms.ModelChoiceField(
        queryset=Estagio.objects.none(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Vaga de Estágio',
        empty_label='Selecione uma vaga'
    )
    
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Observações adicionais (opcional)',
            'rows': 2
        }),
        label='Observações'
    )
    
    def __init__(self, *args, **kwargs):
        # Extrai o parâmetro instituicao antes de chamar super()
        self.instituicao = kwargs.pop('instituicao', None)
        super().__init__(*args, **kwargs)
        
        # CA4 - Exibe apenas vagas disponíveis (aprovadas e com status_vaga='disponivel')
        self.fields['vaga'].queryset = Estagio.objects.filter(
            status='aprovado',
            status_vaga='disponivel'
        ).select_related('empresa', 'supervisor')
        
        # Exibe apenas alunos que não possuem vaga ativa (CA5)
        # Filtra pela instituição do coordenador se fornecida
        alunos_queryset = Aluno.objects.filter(
            estagio__isnull=True
        ).select_related('usuario', 'instituicao')
        
        if self.instituicao:
            alunos_queryset = alunos_queryset.filter(instituicao=self.instituicao)
        
        self.fields['aluno'].queryset = alunos_queryset
    
    def clean_aluno(self):
        aluno = self.cleaned_data.get('aluno')
        if aluno and aluno.estagio is not None:
            # CA5 - Permite apenas uma vaga ativa por aluno
            raise ValidationError(
                f'O aluno {aluno.nome} já está vinculado à vaga "{aluno.estagio.titulo}". '
                'Apenas uma vaga ativa é permitida por aluno.'
            )
        return aluno
    
    def clean_vaga(self):
        vaga = self.cleaned_data.get('vaga')
        if vaga:
            # CA4 - Verifica se a vaga está disponível
            if not vaga.is_disponivel():
                raise ValidationError(
                    'Esta vaga não está mais disponível para vínculo.'
                )
        return vaga
    
    def clean(self):
        cleaned_data = super().clean()
        aluno = cleaned_data.get('aluno')
        vaga = cleaned_data.get('vaga')
        
        if aluno and vaga:
            # CA6 - Impede vínculo duplicado
            from estagio.models import VinculoHistorico
            
            vinculo_existente = VinculoHistorico.objects.filter(
                aluno=aluno,
                estagio=vaga,
                acao='vinculado'
            ).exists()
            
            # Verifica se foi desvinculado depois (pode vincular novamente)
            if vinculo_existente:
                ultimo_vinculo = VinculoHistorico.objects.filter(
                    aluno=aluno,
                    estagio=vaga
                ).order_by('-data_hora').first()
                
                if ultimo_vinculo and ultimo_vinculo.acao == 'vinculado':
                    raise ValidationError(
                        f'O aluno {aluno.nome} já possui um vínculo ativo com esta vaga.'
                    )
        
        return cleaned_data


class AvaliacaoForm(forms.ModelForm):
    """
    Formulário para criar/editar avaliação de desempenho.
    CA1 - Permite avaliação com critérios previamente definidos
    CA2 - Salvamento associado ao período correto
    """
    
    class Meta:
        from .models import Avaliacao
        model = Avaliacao
        fields = ['periodo', 'periodo_inicio', 'periodo_fim', 'parecer']
        widgets = {
            'periodo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'periodo_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'periodo_fim': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'parecer': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Parecer geral sobre o desempenho do estagiário',
                'rows': 4
            }),
        }
        labels = {
            'periodo': 'Tipo de Período',
            'periodo_inicio': 'Início do Período',
            'periodo_fim': 'Fim do Período',
            'parecer': 'Parecer Geral',
        }
    
    def clean_periodo_inicio(self):
        periodo_inicio = self.cleaned_data.get('periodo_inicio')
        if periodo_inicio and periodo_inicio > date.today():
            raise ValidationError('A data de início do período não pode ser futura.')
        return periodo_inicio
    
    def clean_periodo_fim(self):
        periodo_fim = self.cleaned_data.get('periodo_fim')
        periodo_inicio = self.cleaned_data.get('periodo_inicio')
        
        if periodo_fim and periodo_fim > date.today():
            raise ValidationError('A data de fim do período não pode ser futura.')
        
        if periodo_inicio and periodo_fim and periodo_fim < periodo_inicio:
            raise ValidationError('A data de fim deve ser posterior à data de início.')
        
        return periodo_fim
    
    def clean(self):
        cleaned_data = super().clean()
        periodo_inicio = cleaned_data.get('periodo_inicio')
        periodo_fim = cleaned_data.get('periodo_fim')
        
        # Verifica se já existe avaliação para o mesmo período (na edição, ignora a própria)
        if periodo_inicio and periodo_fim and hasattr(self, 'instance') and self.instance:
            from .models import Avaliacao
            
            qs = Avaliacao.objects.filter(
                estagio=self.instance.estagio,
                aluno=self.instance.aluno,
                periodo_inicio=periodo_inicio,
                periodo_fim=periodo_fim
            )
            
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    'Já existe uma avaliação para este aluno no período selecionado.'
                )
        
        return cleaned_data


class NotaCriterioForm(forms.Form):
    """
    Formulário dinâmico para notas de critérios - CA1, CA3
    """
    nota = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0',
            'max': '10'
        })
    )
    observacao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Observações sobre este critério (opcional)'
        })
    )
    
    def __init__(self, *args, criterio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.criterio = criterio
        
        if criterio:
            self.fields['nota'].widget.attrs['min'] = criterio.nota_minima
            self.fields['nota'].widget.attrs['max'] = criterio.nota_maxima
            self.fields['nota'].label = criterio.nome
            self.fields['nota'].help_text = criterio.descricao
            
            if criterio.obrigatorio:
                self.fields['nota'].required = True
                self.fields['nota'].widget.attrs['required'] = True
    
    def clean_nota(self):
        nota = self.cleaned_data.get('nota')
        
        if self.criterio and nota is not None:
            if nota < self.criterio.nota_minima:
                raise ValidationError(
                    f'A nota deve ser maior ou igual a {self.criterio.nota_minima}'
                )
            if nota > self.criterio.nota_maxima:
                raise ValidationError(
                    f'A nota deve ser menor ou igual a {self.criterio.nota_maxima}'
                )
        
        # CA3 - Valida critério obrigatório
        if self.criterio and self.criterio.obrigatorio and nota is None:
            raise ValidationError(
                f'O critério "{self.criterio.nome}" é obrigatório.'
            )
        
        return nota


class AvaliacaoCompletaForm(forms.Form):
    """
    Formulário para validar avaliação completa antes do envio - CA3
    """
    confirmar_envio = forms.BooleanField(
        required=True,
        label='Confirmo que revisei todos os critérios e desejo enviar a avaliação',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, avaliacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.avaliacao = avaliacao
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.avaliacao:
            # CA3 - Impede envio de avaliação incompleta
            if not self.avaliacao.is_completa():
                criterios_faltantes = self.avaliacao.get_criterios_faltantes()
                nomes = ', '.join([c.nome for c in criterios_faltantes])
                raise ValidationError(
                    f'Avaliação incompleta. Critérios faltantes: {nomes}'
                )
        
        return cleaned_data


class ParecerFinalForm(forms.Form):
    """
    Formulário para emissão do parecer final pelo supervisor.
    CA4 - Gera nota automática (exibida no form, mas calculada no backend)
    CA5 - Parecer textual obrigatório
    CA6 - Controle de disponibilização para consulta
    """
    parecer_final = forms.CharField(
        required=True,
        min_length=50,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Digite o parecer final sobre o desempenho do estagiário. '
                          'O parecer deve conter pelo menos 50 caracteres e deve incluir '
                          'uma análise do desempenho geral, pontos fortes, pontos a melhorar '
                          'e recomendações.'
        }),
        label='Parecer Final',
        help_text='O parecer é obrigatório e deve ter no mínimo 50 caracteres.'
    )
    
    disponibilizar_consulta = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Disponibilizar parecer para consulta pelo aluno',
        help_text='Se marcado, o aluno poderá consultar o parecer e a nota final.'
    )
    
    confirmar_emissao = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Confirmo que revisei a avaliação e desejo emitir o parecer final',
        help_text='Após a emissão, o parecer não poderá ser alterado.'
    )
    
    def __init__(self, *args, avaliacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.avaliacao = avaliacao
        
        # Mostra nota calculada se avaliação fornecida
        if avaliacao:
            nota_calculada = avaliacao.calcular_nota_media()
            if nota_calculada:
                self.nota_preview = nota_calculada
    
    def clean_parecer_final(self):
        """CA5 - Valida parecer obrigatório"""
        parecer = self.cleaned_data.get('parecer_final')
        
        if not parecer or not parecer.strip():
            raise ValidationError('O parecer final é obrigatório.')
        
        parecer = parecer.strip()
        
        if len(parecer) < 50:
            raise ValidationError(
                f'O parecer deve ter no mínimo 50 caracteres. '
                f'Atualmente possui {len(parecer)} caracteres.'
            )
        
        return parecer
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.avaliacao:
            # Verifica se avaliação está em estado válido
            if self.avaliacao.status == 'parecer_emitido':
                raise ValidationError(
                    'O parecer final já foi emitido para esta avaliação.'
                )
            
            if self.avaliacao.status not in ['completa', 'enviada']:
                raise ValidationError(
                    'A avaliação deve estar completa para emitir o parecer final.'
                )
            
            # Verifica se há notas para calcular
            nota = self.avaliacao.calcular_nota_media()
            if nota is None:
                raise ValidationError(
                    'Não há notas suficientes para calcular a nota final.'
                )
        
        return cleaned_data


class RelatorioEstagiosForm(forms.Form):
    """
    Formulário para geração de relatórios de estágios com filtros configuráveis.
    CA1 - Filtros configuráveis
    CA2 - Inclusão de dados completos
    CA3 - Validação de período
    
    US: Geração de relatórios dos estágios
    """
    
    # Filtros de período - CA3
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data Início',
        help_text='Data inicial do período para geração do relatório'
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data Fim',
        help_text='Data final do período para geração do relatório'
    )
    
    # Filtros de status - CA1
    STATUS_CHOICES = [
        ('', 'Todos os status'),
        ('analise', 'Em análise'),
        ('em_andamento', 'Em andamento'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Status do Estágio'
    )
    
    # Filtros por empresa - CA1
    empresa = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Empresa',
        empty_label='Todas as empresas'
    )
    
    # Filtros por supervisor - CA1
    supervisor = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Supervisor',
        empty_label='Todos os supervisores'
    )
    
    # Filtros por instituição - CA1
    instituicao = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Instituição',
        empty_label='Todas as instituições'
    )
    
    # Opções de inclusão de dados - CA2
    incluir_documentos = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir informações de documentos'
    )
    
    incluir_avaliacoes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir avaliações'
    )
    
    incluir_horas = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir horas cumpridas'
    )
    
    incluir_aluno = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir dados do aluno'
    )
    
    # Formato de exportação
    FORMATO_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
    ]
    
    formato = forms.ChoiceField(
        choices=FORMATO_CHOICES,
        required=False,
        initial='json',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Formato de Exportação'
    )
    
    def __init__(self, *args, **kwargs):
        from admin.models import Empresa, Supervisor, Instituicao
        super().__init__(*args, **kwargs)
        self.fields['empresa'].queryset = Empresa.objects.all()
        self.fields['supervisor'].queryset = Supervisor.objects.all()
        self.fields['instituicao'].queryset = Instituicao.objects.all()
    
    def clean(self):
        """
        CA3 - Validação de período informado
        """
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        # Validação: se uma data foi informada, a outra também deve ser
        if data_inicio and not data_fim:
            raise ValidationError(
                {'data_fim': 'Informe a data fim para completar o período.'}
            )
        
        if data_fim and not data_inicio:
            raise ValidationError(
                {'data_inicio': 'Informe a data início para completar o período.'}
            )
        
        # CA3 - Validação: data fim não pode ser anterior à data início
        if data_inicio and data_fim:
            if data_fim < data_inicio:
                raise ValidationError(
                    {'data_fim': 'A data fim não pode ser anterior à data início.'}
                )
            
            # Validação: período máximo de 1 ano
            from datetime import timedelta
            if (data_fim - data_inicio).days > 365:
                raise ValidationError(
                    {'data_fim': 'O período máximo permitido é de 1 ano (365 dias).'}
                )
            
            # Validação: data fim não pode ser futura
            if data_fim > date.today():
                raise ValidationError(
                    {'data_fim': 'A data fim não pode ser uma data futura.'}
                )
        
        return cleaned_data
    
    def get_filtros_ativos(self):
        """
        Retorna dicionário com os filtros ativos para exibição no relatório.
        CA1 - Permite identificar quais filtros foram aplicados
        """
        filtros = {}
        
        if self.cleaned_data.get('data_inicio'):
            filtros['periodo'] = {
                'inicio': self.cleaned_data['data_inicio'],
                'fim': self.cleaned_data['data_fim']
            }
        
        if self.cleaned_data.get('status'):
            filtros['status'] = self.cleaned_data['status']
        
        if self.cleaned_data.get('empresa'):
            filtros['empresa'] = str(self.cleaned_data['empresa'])
        
        if self.cleaned_data.get('supervisor'):
            filtros['supervisor'] = str(self.cleaned_data['supervisor'])
        
        if self.cleaned_data.get('instituicao'):
            filtros['instituicao'] = str(self.cleaned_data['instituicao'])
        
        return filtros
    
    def get_opcoes_inclusao(self):
        """
        CA2 - Retorna as opções de inclusão de dados selecionadas
        """
        return {
            'documentos': self.cleaned_data.get('incluir_documentos', True),
            'avaliacoes': self.cleaned_data.get('incluir_avaliacoes', True),
            'horas': self.cleaned_data.get('incluir_horas', True),
            'aluno': self.cleaned_data.get('incluir_aluno', True),
        }