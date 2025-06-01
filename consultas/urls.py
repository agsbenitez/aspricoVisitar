from django.urls import path
from .views import NuevaConsultaView

app_name = 'consultas'

urlpatterns = [
    path('nueva/', NuevaConsultaView.as_view(), name='nueva_consulta'),
] 