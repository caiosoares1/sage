"""
Comando de gerenciamento para gerar dados falsos usando Faker.
Útil para testar paginação e visualização de dados em massa.

Uso:
    python manage.py generate_fake_data
    python manage.py generate_fake_data --clear  # Limpa dados existentes antes
    python manage.py generate_fake_data --instituicoes 10 --empresas 20 --alunos 50
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from admin.models import Instituicao, Empresa, Supervisor, CursoCoordenador
from estagio.models import Aluno, Estagio
from datetime import date, timedelta
import random

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Gera dados falsos para testar paginação usando a biblioteca Faker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa os dados existentes antes de gerar novos',
        )
        parser.add_argument(
            '--instituicoes',
            type=int,
            default=15,
            help='Número de instituições a criar (padrão: 15)',
        )
        parser.add_argument(
            '--empresas',
            type=int,
            default=25,
            help='Número de empresas a criar (padrão: 25)',
        )
        parser.add_argument(
            '--supervisores',
            type=int,
            default=30,
            help='Número de supervisores a criar (padrão: 30)',
        )
        parser.add_argument(
            '--coordenadores',
            type=int,
            default=10,
            help='Número de coordenadores a criar (padrão: 10)',
        )
        parser.add_argument(
            '--alunos',
            type=int,
            default=50,
            help='Número de alunos a criar (padrão: 50)',
        )
        parser.add_argument(
            '--estagios',
            type=int,
            default=40,
            help='Número de estágios a criar (padrão: 40)',
        )
        parser.add_argument(
            '--atividades',
            type=int,
            default=60,
            help='Número de atividades a criar (padrão: 60)',
        )

    def handle(self, *args, **options):
        if not FAKER_AVAILABLE:
            self.stdout.write(
                self.style.ERROR(
                    'Biblioteca Faker não encontrada. Instale com: pip install faker'
                )
            )
            return

        fake = Faker('pt_BR')  # Faker em português brasileiro
        
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando geração de dados falsos...'))

        if options['clear']:
            self.stdout.write(self.style.WARNING('⚠️  Limpando dados existentes...'))
            from estagio.models import Atividade
            Atividade.objects.all().delete()
            Aluno.objects.all().delete()
            Estagio.objects.all().delete()
            CursoCoordenador.objects.all().delete()
            Supervisor.objects.all().delete()
            Empresa.objects.all().delete()
            Instituicao.objects.all().delete()
            Usuario.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('✅ Dados limpos com sucesso!'))

        # Gerar Instituições
        instituicoes = self._criar_instituicoes(fake, options['instituicoes'])
        
        # Gerar Empresas
        empresas = self._criar_empresas(fake, options['empresas'])
        
        # Gerar Supervisores (requer empresas)
        supervisores = self._criar_supervisores(fake, empresas, options['supervisores'])
        
        # Gerar Coordenadores (requer instituições)
        coordenadores = self._criar_coordenadores(fake, instituicoes, options['coordenadores'])
        
        # Gerar Estágios (requer empresas e supervisores)
        estagios = self._criar_estagios(fake, empresas, supervisores, options['estagios'])
        
        # Gerar Alunos (requer instituições)
        alunos = self._criar_alunos(fake, instituicoes, estagios, options['alunos'])
        
        # Gerar Atividades (requer alunos com estágio)
        atividades = self._criar_atividades(fake, alunos, options['atividades'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('📊 RESUMO DOS DADOS GERADOS:'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'   📍 Instituições: {len(instituicoes)}')
        self.stdout.write(f'   🏢 Empresas: {len(empresas)}')
        self.stdout.write(f'   👔 Supervisores: {len(supervisores)}')
        self.stdout.write(f'   🎓 Coordenadores: {len(coordenadores)}')
        self.stdout.write(f'   📋 Estágios: {len(estagios)}')
        self.stdout.write(f'   👨‍🎓 Alunos: {len(alunos)}')
        self.stdout.write(f'   📝 Atividades: {len(atividades)}')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Dados gerados com sucesso!'))
        self.stdout.write(self.style.SUCCESS('💡 Agora você pode testar a paginação nas listagens.'))

    def _criar_instituicoes(self, fake, quantidade):
        """Cria instituições de ensino"""
        self.stdout.write(f'📍 Criando {quantidade} instituições...')
        
        tipos = ['Universidade', 'Instituto Federal', 'Faculdade', 'Centro Universitário', 'Instituto']
        sufixos = ['de Tecnologia', 'de Ciências', 'de Educação', 'Técnico', 'Superior']
        
        instituicoes = []
        for i in range(quantidade):
            tipo = random.choice(tipos)
            cidade = fake.city()
            
            instituicao = Instituicao.objects.create(
                nome=f'{tipo} {cidade}'[:150],
                contato=fake.phone_number()[:90],
                rua=fake.street_name()[:50],
                numero=int(fake.building_number()) % 10000,
                bairro=fake.bairro()[:30]
            )
            instituicoes.append(instituicao)
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(instituicoes)} instituições criadas'))
        return instituicoes

    def _criar_empresas(self, fake, quantidade):
        """Cria empresas"""
        self.stdout.write(f'🏢 Criando {quantidade} empresas...')
        
        setores = ['Tech', 'Solutions', 'Systems', 'Digital', 'Software', 'Consulting', 'Labs', 'Data', 'Cloud', 'AI']
        tipos = ['Ltda', 'S.A.', 'EIRELI', 'ME', 'EPP']
        
        empresas = []
        for i in range(quantidade):
            setor = random.choice(setores)
            
            empresa = Empresa.objects.create(
                cnpj=fake.cnpj().replace('.', '').replace('/', '').replace('-', ''),
                razao_social=f'{fake.company()} {setor} {random.choice(tipos)}'[:150],
                rua=fake.street_name()[:50],
                numero=int(fake.building_number()) % 10000,
                bairro=fake.bairro()[:30]
            )
            empresas.append(empresa)
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(empresas)} empresas criadas'))
        return empresas

    def _criar_supervisores(self, fake, empresas, quantidade):
        """Cria supervisores vinculados às empresas"""
        self.stdout.write(f'👔 Criando {quantidade} supervisores...')
        
        cargos = [
            'Gerente de TI', 'Coordenador de Projetos', 'Tech Lead', 
            'Gerente de Desenvolvimento', 'Supervisor de Estágios',
            'Diretor de Tecnologia', 'Líder Técnico', 'Gerente de Operações',
            'Coordenador de RH', 'Gerente de Inovação'
        ]
        
        supervisores = []
        for i in range(quantidade):
            nome = fake.name()
            email = fake.email()
            username = email.split('@')[0] + str(i)
            
            # Criar usuário
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password='senha123',
                tipo='supervisor',
                first_name=nome.split()[0],
                last_name=' '.join(nome.split()[1:]) if len(nome.split()) > 1 else ''
            )
            
            # Criar supervisor
            supervisor = Supervisor.objects.create(
                nome=nome,
                cargo=random.choice(cargos),
                contato=fake.phone_number(),
                usuario=usuario,
                empresa=random.choice(empresas)
            )
            supervisores.append(supervisor)
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(supervisores)} supervisores criados'))
        return supervisores

    def _criar_coordenadores(self, fake, instituicoes, quantidade):
        """Cria coordenadores de curso"""
        self.stdout.write(f'🎓 Criando {quantidade} coordenadores...')
        
        cursos = [
            'Ciência da Computação', 'Engenharia de Software', 'Sistemas de Informação',
            'Análise e Desenvolvimento de Sistemas', 'Redes de Computadores',
            'Engenharia da Computação', 'Tecnologia da Informação', 'Banco de Dados',
            'Segurança da Informação', 'Inteligência Artificial'
        ]
        
        coordenadores = []
        for i in range(quantidade):
            nome = fake.name()
            email = f'coord.{i}@{fake.domain_name()}'
            username = f'coord_{i}'
            
            # Criar usuário
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password='senha123',
                tipo='coordenador',
                first_name=nome.split()[0],
                last_name=' '.join(nome.split()[1:]) if len(nome.split()) > 1 else ''
            )
            
            # Criar coordenador
            coordenador = CursoCoordenador.objects.create(
                nome=nome,
                contato=fake.phone_number(),
                carga_horaria=random.choice([200, 300, 400, 500, 600]),
                nome_curso=cursos[i % len(cursos)],
                codigo_curso=1000 + i,
                usuario=usuario,
                instituicao=random.choice(instituicoes)
            )
            coordenadores.append(coordenador)
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(coordenadores)} coordenadores criados'))
        return coordenadores

    def _criar_estagios(self, fake, empresas, supervisores, quantidade):
        """Cria estágios"""
        self.stdout.write(f'📋 Criando {quantidade} estágios...')
        
        titulos = [
            'Estágio em Dev', 'Estágio TI', 'Dev Jr', 'Suporte TI',
            'Analista Jr', 'Dev Backend', 'Dev Frontend', 'DevOps Jr',
            'Data Intern', 'QA Intern', 'UX Intern', 'Infra TI'
        ]
        
        cargos = [
            'Desenvolvedor Júnior', 'Analista de Sistemas', 'Programador',
            'Suporte Técnico', 'Analista de Dados', 'Desenvolvedor Web',
            'Analista de Qualidade', 'Designer UX/UI', 'DevOps', 'DBA Júnior'
        ]
        
        status_choices = ['analise', 'em_andamento', 'aprovado', 'reprovado']
        status_vaga_choices = ['disponivel', 'ocupada', 'encerrada']
        
        estagios = []
        for i in range(quantidade):
            data_inicio = fake.date_between(start_date='-6m', end_date='+1m')
            data_fim = data_inicio + timedelta(days=random.randint(90, 365))
            
            estagio = Estagio.objects.create(
                titulo=random.choice(titulos)[:30],  # max 30 chars
                cargo=random.choice(cargos),
                data_inicio=data_inicio,
                data_fim=data_fim,
                carga_horaria=random.choice([20, 25, 30, 40]),
                descricao=fake.paragraph(nb_sentences=3),
                empresa=random.choice(empresas),
                supervisor=random.choice(supervisores),
                status=random.choice(status_choices),
                status_vaga=random.choice(status_vaga_choices)
            )
            estagios.append(estagio)
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(estagios)} estágios criados'))
        return estagios

    def _criar_alunos(self, fake, instituicoes, estagios, quantidade):
        """Cria alunos"""
        self.stdout.write(f'👨‍🎓 Criando {quantidade} alunos...')
        
        # Filtrar estágios disponíveis para vincular
        estagios_disponiveis = [e for e in estagios if e.status_vaga == 'disponivel']
        
        alunos = []
        for i in range(quantidade):
            nome = fake.name()
            email = f'aluno.{i}@{fake.domain_name()}'
            username = f'aluno_{i}'
            
            # Criar usuário
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password='senha123',
                tipo='aluno',
                first_name=nome.split()[0],
                last_name=' '.join(nome.split()[1:]) if len(nome.split()) > 1 else ''
            )
            
            # Decidir se vincula a um estágio (30% de chance)
            estagio = None
            if estagios_disponiveis and random.random() < 0.3:
                estagio = random.choice(estagios_disponiveis)
                estagios_disponiveis.remove(estagio)  # Evitar duplicação
            
            # Criar aluno
            aluno = Aluno.objects.create(
                nome=nome,
                contato=fake.phone_number(),
                matricula=str(2020000000 + i),
                usuario=usuario,
                instituicao=random.choice(instituicoes),
                estagio=estagio
            )
            alunos.append(aluno)
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(alunos)} alunos criados'))
        
        # Vincular alunos como solicitantes em estágios com status 'analise'
        estagios_analise = Estagio.objects.filter(status='analise', aluno_solicitante__isnull=True)
        alunos_sem_solicitacao = list(alunos)  # Cópia para não modificar a lista original
        
        for estagio in estagios_analise:
            if alunos_sem_solicitacao:
                aluno = random.choice(alunos_sem_solicitacao)
                estagio.aluno_solicitante = aluno
                estagio.data_solicitacao = timezone.now() - timedelta(days=random.randint(1, 30))
                estagio.save()
                alunos_sem_solicitacao.remove(aluno)  # Cada aluno só pode solicitar um
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ Vinculados {estagios_analise.count()} solicitantes a estágios em análise'))
        
        return alunos

    def _criar_atividades(self, fake, alunos, quantidade):
        """Cria atividades para os alunos com estágio vinculado"""
        self.stdout.write(f'📝 Criando {quantidade} atividades...')
        
        from estagio.models import Atividade
        from datetime import date
        
        titulos_atividades = [
            'Desenvolvimento de API REST',
            'Implementação de testes unitários',
            'Criação de documentação técnica',
            'Análise de requisitos',
            'Reunião de alinhamento',
            'Correção de bugs',
            'Code review',
            'Deploy em produção',
            'Configuração de ambiente',
            'Estudo de novas tecnologias',
            'Desenvolvimento de frontend',
            'Integração com sistemas externos',
            'Otimização de performance',
            'Criação de relatórios',
            'Treinamento interno',
        ]
        
        descricoes = [
            'Realizei as atividades conforme solicitado pelo supervisor.',
            'Trabalhei no desenvolvimento das funcionalidades planejadas.',
            'Participei ativamente das reuniões e contribuí com sugestões.',
            'Finalizei as tarefas dentro do prazo estabelecido.',
            'Colaborei com a equipe na resolução de problemas técnicos.',
        ]
        
        status_choices = ['pendente', 'confirmada', 'rejeitada']
        status_weights = [0.6, 0.3, 0.1]  # 60% pendente, 30% confirmada, 10% rejeitada
        
        # Filtrar apenas alunos com estágio vinculado
        alunos_com_estagio = [a for a in alunos if a.estagio is not None]
        
        if not alunos_com_estagio:
            self.stdout.write(self.style.WARNING('   ⚠️ Nenhum aluno com estágio vinculado para criar atividades'))
            return []
        
        atividades = []
        for i in range(quantidade):
            aluno = random.choice(alunos_com_estagio)
            status = random.choices(status_choices, weights=status_weights)[0]
            
            data_realizacao = fake.date_between(start_date='-30d', end_date='today')
            
            atividade = Atividade.objects.create(
                aluno=aluno,
                estagio=aluno.estagio,
                titulo=random.choice(titulos_atividades),
                descricao=random.choice(descricoes) + ' ' + fake.paragraph(nb_sentences=2),
                data_realizacao=data_realizacao,
                horas_dedicadas=random.randint(1, 8),
                status=status,
                confirmado_por=aluno.estagio.supervisor if status != 'pendente' else None,
                data_confirmacao=timezone.now() - timedelta(days=random.randint(0, 10)) if status != 'pendente' else None,
                justificativa_rejeicao='Atividade não corresponde ao plano de estágio.' if status == 'rejeitada' else None
            )
            atividades.append(atividade)
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(atividades)} atividades criadas'))
        return atividades
