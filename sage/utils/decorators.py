from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(view_func):
    """Decorator para garantir que apenas administradores possam acessar a view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Verifica se o usuário é administrador
        is_admin = (
            request.user.is_superuser or 
            getattr(request.user, 'tipo', None) == 'admin'
        )
        
        if not is_admin:
            messages.error(request, 'Acesso negado. Esta área é restrita a administradores.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def _is_admin(user):
    """Verifica se o usuário é administrador"""
    return user.is_superuser or getattr(user, 'tipo', None) == 'admin'


def supervisor_required(view_func):
    """Decorator para garantir que apenas supervisores (ou admins) possam acessar a view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Admins têm acesso a tudo
        if _is_admin(request.user):
            return view_func(request, *args, **kwargs)
        
        # Verifica se o usuário é um supervisor
        if not hasattr(request.user, 'supervisor'):
            messages.error(request, 'Acesso negado. Esta área é restrita a supervisores.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def coordenador_required(view_func):
    """Decorator para garantir que apenas coordenadores (ou admins) possam acessar a view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Admins têm acesso a tudo
        if _is_admin(request.user):
            return view_func(request, *args, **kwargs)
        
        # Verifica se o usuário é um coordenador
        if not hasattr(request.user, 'cursocoordenador'):
            messages.error(request, 'Acesso negado. Esta área é restrita a coordenadores.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def coordenador_only_required(view_func):
    """Decorator para garantir que APENAS coordenadores possam acessar a view (sem admin)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Verifica se o usuário é um coordenador
        if not hasattr(request.user, 'cursocoordenador'):
            messages.error(request, 'Acesso negado. Esta área é restrita a coordenadores.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def aluno_required(view_func):
    """Decorator para garantir que apenas alunos (ou admins) possam acessar a view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Admins têm acesso a tudo
        if _is_admin(request.user):
            return view_func(request, *args, **kwargs)
        
        # Verifica se o usuário é um aluno
        if not hasattr(request.user, 'aluno'):
            messages.error(request, 'Acesso negado. Esta área é restrita a alunos.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper
