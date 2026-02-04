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
                nome=f'{tipo} {cidade}',
                contato=fake.phone_number(),
                rua=fake.street_name(),
                numero=fake.building_number(),
                bairro=fake.bairro()
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
                razao_social=f'{fake.company()} {setor} {random.choice(tipos)}',
                rua=fake.street_name(),
                numero=int(fake.building_number()),
                bairro=fake.bairro()
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
        return alunos
