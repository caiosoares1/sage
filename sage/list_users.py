#!/usr/bin/env python
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sage.settings')

import django
django.setup()

from users.models import Usuario
from estagio.models import Aluno, Atividade, Estagio
from admin.models import Supervisor

print('=' * 60)
print('SUPERVISORES')
print('=' * 60)
for u in Usuario.objects.filter(tipo='supervisor').order_by('username')[:15]:
    print(f'  Username: {u.username:<30} | Email: {u.email}')
total_sup = Usuario.objects.filter(tipo='supervisor').count()
print(f'  ... Total: {total_sup} supervisores')

print()
print('=' * 60)
print('COORDENADORES')
print('=' * 60)
for u in Usuario.objects.filter(tipo='coordenador').order_by('username'):
    print(f'  Username: {u.username:<30} | Email: {u.email}')
total_coord = Usuario.objects.filter(tipo='coordenador').count()
print(f'  ... Total: {total_coord} coordenadores')

print()
print('=' * 60)
print('ALUNOS')
print('=' * 60)
for u in Usuario.objects.filter(tipo='aluno').order_by('username')[:15]:
    print(f'  Username: {u.username:<30} | Email: {u.email}')
total_alunos = Usuario.objects.filter(tipo='aluno').count()
print(f'  ... Total: {total_alunos} alunos')

print()
print('=' * 60)
print('STATUS DOS DADOS')
print('=' * 60)
print(f'  Total alunos: {Aluno.objects.count()}')
print(f'  Alunos com estágio: {Aluno.objects.exclude(estagio=None).count()}')
estagios_disp = Estagio.objects.filter(status='aprovado', status_vaga='disponivel').count()
print(f'  Estágios aprovados disponíveis: {estagios_disp}')
print(f'  Total atividades: {Atividade.objects.count()}')
print(f'  Atividades pendentes: {Atividade.objects.filter(status="pendente").count()}')

print()
print('=' * 60)
print('SUPERVISORES COM ATIVIDADES')
print('=' * 60)
for s in Supervisor.objects.all()[:10]:
    count = Atividade.objects.filter(estagio__supervisor=s).count()
    if count > 0:
        print(f'  {s.usuario.username}: {count} atividades')

print()
print('=' * 60)
print('SENHA PADRAO PARA TODOS: senha123')
print('=' * 60)
