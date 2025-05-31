from django.urls import path
from . import views

app_name = 'afiliados'

urlpatterns = [
    path('importar/', views.ImportarAfiliadosView.as_view(), name='importar_afiliados'),
] 