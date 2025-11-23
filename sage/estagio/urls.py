from django.urls import path
from . import views

urlpatterns = [
    path('solicitar/', views.solicitar_estagio, name='solicitar_estagio'),
    path('acompanhar/', views.acompanhar_estagios, name='acompanhar_estagios'),
    path('detalhe/<int:estagio_id>/', views.estagio_detalhe, name='estagio_detalhe'),
]
