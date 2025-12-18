from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admin.models import Instituicao
from estagio.models import Aluno

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Create a student profile for an existing user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        
        try:
            usuario = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} not found'))
            return

        # Check if student already exists
        if Aluno.objects.filter(usuario=usuario).exists():
            self.stdout.write(self.style.WARNING(f'Student profile already exists for {username}'))
            return

        # Get or create institution
        inst, created = Instituicao.objects.get_or_create(
            nome='Universidade Federal de Exemplo',
            defaults={
                'contato': '(11) 3333-4444',
                'rua': 'Av. Universitária',
                'numero': 1000,
                'bairro': 'Centro'
            }
        )

        # Create student
        aluno = Aluno.objects.create(
            nome=f'{usuario.first_name} {usuario.last_name}' if usuario.first_name else usuario.username,
            contato=usuario.email or f'{usuario.username}@exemplo.com',
            matricula=f'2025{usuario.id:04d}',
            usuario=usuario,
            instituicao=inst
        )

        self.stdout.write(self.style.SUCCESS(f'✅ Student profile created for {username}'))
        self.stdout.write(f'  Name: {aluno.nome}')
        self.stdout.write(f'  Matricula: {aluno.matricula}')
        self.stdout.write(f'  Institution: {inst.nome}')
