from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admin.models import Instituicao, Empresa, Supervisor, CursoCoordenador
from estagio.models import Aluno, Estagio
from datetime import date, timedelta

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Populates the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))

        # Clear existing data (optional - comment out if you want to keep existing data)
        self.stdout.write('Clearing existing data...')
        Aluno.objects.all().delete()
        Estagio.objects.all().delete()
        CursoCoordenador.objects.all().delete()
        Supervisor.objects.all().delete()
        Empresa.objects.all().delete()
        Instituicao.objects.all().delete()
        Usuario.objects.filter(is_superuser=False).delete()

        # Create Institutions
        self.stdout.write('Creating institutions...')
        inst1 = Instituicao.objects.create(
            nome='Universidade Federal de Exemplo',
            contato='(11) 3333-4444',
            rua='Av. Universitária',
            numero=1000,
            bairro='Centro'
        )
        inst2 = Instituicao.objects.create(
            nome='Instituto Tecnológico',
            contato='(11) 5555-6666',
            rua='Rua da Tecnologia',
            numero=500,
            bairro='Jardim Tech'
        )

        # Create Companies
        self.stdout.write('Creating companies...')
        emp1 = Empresa.objects.create(
            cnpj='12345678000190',
            razao_social='Tech Solutions Ltda',
            rua='Av. Paulista',
            numero=1500,
            bairro='Bela Vista'
        )
        emp2 = Empresa.objects.create(
            cnpj='98765432000110',
            razao_social='DataCorp Sistemas',
            rua='Rua dos Desenvolvedores',
            numero=250,
            bairro='Vila Digital'
        )
        emp3 = Empresa.objects.create(
            cnpj='11223344000155',
            razao_social='StartupHub Inovação',
            rua='Alameda das Startups',
            numero=100,
            bairro='Jardim Empreendedor'
        )

        # Create Supervisor Users
        self.stdout.write('Creating supervisor users...')
        user_sup1 = Usuario.objects.create_user(
            username='miguel.santos',
            email='miguel@techsolutions.com',
            password='senha123',
            tipo='supervisor',
            first_name='Miguel',
            last_name='Santos'
        )
        user_sup2 = Usuario.objects.create_user(
            username='ana.oliveira',
            email='ana@datacorp.com',
            password='senha123',
            tipo='supervisor',
            first_name='Ana',
            last_name='Oliveira'
        )
        user_sup3 = Usuario.objects.create_user(
            username='carlos.mendes',
            email='carlos@startuphub.com',
            password='senha123',
            tipo='supervisor',
            first_name='Carlos',
            last_name='Mendes'
        )

        # Create Supervisors
        self.stdout.write('Creating supervisors...')
        sup1 = Supervisor.objects.create(
            nome='Miguel Santos',
            cargo='Gerente de TI',
            contato='(11) 9999-1111',
            usuario=user_sup1,
            empresa=emp1
        )
        sup2 = Supervisor.objects.create(
            nome='Ana Oliveira',
            cargo='Coordenadora de Projetos',
            contato='(11) 9999-2222',
            usuario=user_sup2,
            empresa=emp2
        )
        sup3 = Supervisor.objects.create(
            nome='Carlos Mendes',
            cargo='CTO',
            contato='(11) 9999-3333',
            usuario=user_sup3,
            empresa=emp3
        )

        # Create Coordinator Users
        self.stdout.write('Creating coordinator users...')
        user_coord1 = Usuario.objects.create_user(
            username='prof.silva',
            email='silva@universidade.edu',
            password='senha123',
            tipo='coordenador',
            first_name='Roberto',
            last_name='Silva'
        )
        user_coord2 = Usuario.objects.create_user(
            username='prof.martins',
            email='martins@instituto.edu',
            password='senha123',
            tipo='coordenador',
            first_name='Maria',
            last_name='Martins'
        )

        # Create Coordinators
        self.stdout.write('Creating coordinators...')
        coord1 = CursoCoordenador.objects.create(
            nome='Prof. Roberto Silva',
            nome_curso='Ciência da Computação',
            codigo_curso=1001,
            carga_horaria=40,
            contato='(11) 3333-7777',
            usuario=user_coord1,
            instituicao=inst1
        )
        coord2 = CursoCoordenador.objects.create(
            nome='Profa. Maria Martins',
            nome_curso='Sistemas de Informação',
            codigo_curso=1002,
            carga_horaria=40,
            contato='(11) 5555-8888',
            usuario=user_coord2,
            instituicao=inst2
        )

        # Create Student Users
        self.stdout.write('Creating student users...')
        user_aluno1 = Usuario.objects.create_user(
            username='caio.batista',
            email='caio@exemplo.com',
            password='senha123',
            tipo='aluno',
            first_name='Caio',
            last_name='Batista'
        )
        user_aluno2 = Usuario.objects.create_user(
            username='julia.costa',
            email='julia@exemplo.com',
            password='senha123',
            tipo='aluno',
            first_name='Julia',
            last_name='Costa'
        )
        user_aluno3 = Usuario.objects.create_user(
            username='pedro.alves',
            email='pedro@exemplo.com',
            password='senha123',
            tipo='aluno',
            first_name='Pedro',
            last_name='Alves'
        )

        # Create Internships
        self.stdout.write('Creating internships...')
        hoje = date.today()
        
        estagio1 = Estagio.objects.create(
            titulo='Estágio em Desenvolvimento Web',
            cargo='Desenvolvedor Junior',
            data_inicio=hoje + timedelta(days=7),
            data_fim=hoje + timedelta(days=187),
            carga_horaria=20,
            empresa=emp1,
            supervisor=sup1,
            status='analise'
        )
        
        estagio2 = Estagio.objects.create(
            titulo='Estágio em Data Science',
            cargo='Analista de Dados Jr',
            data_inicio=hoje + timedelta(days=14),
            data_fim=hoje + timedelta(days=194),
            carga_horaria=30,
            empresa=emp2,
            supervisor=sup2,
            status='aprovado'
        )
        
        estagio3 = Estagio.objects.create(
            titulo='Estágio em DevOps',
            cargo='Assistente de Infraestrutura',
            data_inicio=hoje + timedelta(days=21),
            data_fim=hoje + timedelta(days=201),
            carga_horaria=25,
            empresa=emp3,
            supervisor=sup3,
            status='analise'
        )

        # Create Students and link to internships
        self.stdout.write('Creating students...')
        aluno1 = Aluno.objects.create(
            nome='Caio Batista',
            contato='(11) 9999-4444',
            matricula='20210001',
            usuario=user_aluno1,
            instituicao=inst1,
            estagio=estagio1
        )
        
        aluno2 = Aluno.objects.create(
            nome='Julia Costa',
            contato='(11) 9999-5555',
            matricula='20210002',
            usuario=user_aluno2,
            instituicao=inst2,
            estagio=estagio2
        )
        
        aluno3 = Aluno.objects.create(
            nome='Pedro Alves',
            contato='(11) 9999-6666',
            matricula='20210003',
            usuario=user_aluno3,
            instituicao=inst1,
            estagio=estagio3
        )

        self.stdout.write(self.style.SUCCESS('\n✅ Database populated successfully!\n'))
        self.stdout.write(self.style.SUCCESS('Sample credentials:'))
        self.stdout.write(self.style.SUCCESS('  Students:'))
        self.stdout.write('    - caio.batista / senha123')
        self.stdout.write('    - julia.costa / senha123')
        self.stdout.write('    - pedro.alves / senha123')
        self.stdout.write(self.style.SUCCESS('  Coordinators:'))
        self.stdout.write('    - prof.silva / senha123')
        self.stdout.write('    - prof.martins / senha123')
        self.stdout.write(self.style.SUCCESS('  Supervisors:'))
        self.stdout.write('    - miguel.santos / senha123')
        self.stdout.write('    - ana.oliveira / senha123')
        self.stdout.write('    - carlos.mendes / senha123')
