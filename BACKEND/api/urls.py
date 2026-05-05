from django.urls import path
from . import views

urlpatterns = [
    path('subir/', views.subir_archivo, name='subir-archivo'),
    path('analisis/', views.listar_analisis, name='listar-analisis'),
    path('analisis/<int:pk>/', views.detalle_analisis, name='detalle-analisis'),
    path('analisis/<int:pk>/completo/', views.analisis_completo, name='analisis-completo'),
    path('analisis/<int:pk>/clustering/', views.clustering_analisis, name='clustering-analisis'),
    path('analisis/<int:pk>/heatmap/', views.heatmap_correlacion, name='heatmap-correlacion'),
]
