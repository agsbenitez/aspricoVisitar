# estadisticas/urls.py
from django.urls import path
from . import views

app_name = 'estadisticas' # 🚨 Importante para usar {% url 'estadisticas:dashboard' %}

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/exportar/', views.exportar_consultas_csv, name='exportar_csv'),
]