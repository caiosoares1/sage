from django.urls import path
from . import views

app_name = 'coordenador'

urlpatterns = [
    path('documentos/', views.aprovar_documentos_coordenador, name='documentos'),
    path('documentos/<int:documento_id>/aprovar/', views.aprovar_documento_coordenador, name='aprovar_documento'),
]
