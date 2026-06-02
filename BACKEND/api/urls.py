from django.urls import path
from . import views

urlpatterns = [
    path('subir/', views.subir_archivo, name='subir-archivo'),
    path('analisis/', views.listar_analisis, name='listar-analisis'),
    path('analisis/<int:pk>/', views.detalle_analisis, name='detalle-analisis'),
    path('analisis/<int:pk>/completo/', views.analisis_completo, name='analisis-completo'),
    path('analisis/<int:pk>/clustering/', views.clustering_analisis, name='clustering-analisis'),
    path('analisis/<int:pk>/heatmap/', views.heatmap_correlacion, name='heatmap-correlacion'),
    path('sivigila/resumen/', views.resumen_sivigila, name='resumen-sivigila'),
    path('sivigila/pacientes/', views.listar_pacientes, name='listar-pacientes'),
    path('sivigila/morbilidad/', views.listar_morbilidad_sivigila, name='listar-morbilidad-sivigila'),
    path('sivigila/mortalidad/', views.listar_mortalidad_sivigila, name='listar-mortalidad-sivigila'),
    path('auth/register/', views.register_usuario, name='register-usuario'),
    path('auth/login/', views.login_usuario, name='login-usuario'),
]
