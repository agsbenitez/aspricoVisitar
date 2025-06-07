from django.urls import path
from .views import NuevaConsultaView, imprimir_bono

app_name = 'consultas'

urlpatterns = [
    path('nueva/', NuevaConsultaView.as_view(), name='nueva_consulta'),
    path('imprimir-bono/', imprimir_bono, name='imprimir_bono'),
] 