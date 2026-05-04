from django.urls import path
from . import views

urlpatterns = [
    path('subir/', views.subir_archivo, name='subir-archivo'),
    path('analisis/', views.listar_analisis, name='listar-analisis'),
    path('analisis/<int:pk>/', views.detalle_analisis, name='detalle-analisis'),
]
