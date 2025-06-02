from django.shortcuts import render
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

from .models import Consulta
from .forms import ConsultaForm
from afiliados.models import Afiliado

# Create your views here.

class NuevaConsultaView(LoginRequiredMixin, CreateView):
    model = Consulta
    form_class = ConsultaForm
    template_name = 'consultas/nueva_consulta.html'
    success_url = reverse_lazy('consultas:nueva_consulta')

    def get_initial(self):
        """Establece valores iniciales para el formulario"""
        initial = super().get_initial()
        initial['prestador'] = 'RED ASPRICO ACE'
        initial['fecha_emision'] = timezone.now()
        return initial

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto"""
        context = super().get_context_data(**kwargs)
        # Si es una nueva consulta (GET), creamos un objeto temporal para mostrar
        if self.request.method == 'GET':
            context['consulta'] = Consulta(
                fecha_emision=timezone.now(),
                prestador='RED ASPRICO ACE',
                nro_de_orden=Consulta.objects.count() + 1  # Número tentativo
            )
        return context

    def form_valid(self, form):
        """Procesa el formulario válido"""
        logger.info('Iniciando form_valid en NuevaConsultaView')
        form.instance.usuario = self.request.user
        form.instance.fecha_emision = timezone.now()
        form.instance.prestador = 'RED ASPRICO ACE'
        logger.info(f'Datos del formulario: {form.cleaned_data}')
        response = super().form_valid(form)
        logger.info(f'Consulta creada con ID: {form.instance.nro_de_orden}')
        return response

    def form_invalid(self, form):
        """Log de errores cuando el formulario es inválido"""
        logger.error(f'Errores en el formulario: {form.errors}')
        return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        """Maneja las peticiones POST, incluyendo búsquedas AJAX"""
        logger.info(f'Método POST recibido - Es AJAX: {request.headers.get("X-Requested-With") == "XMLHttpRequest"}')
        logger.info(f'Datos POST recibidos: {request.POST}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Es una petición AJAX para buscar afiliados
            termino = request.POST.get('buscar_afiliado', '').strip()
            if termino:
                afiliados = Afiliado.objects.filter(
                    Q(nombre__icontains=termino) |
                    Q(nrodoc__icontains=termino) |
                    Q(cuil__icontains=termino)
                )[:10]  # Limitamos a 10 resultados
                
                resultados = [{
                    'id': afiliado.id,
                    'nombre': afiliado.nombre,
                    'nrodoc': afiliado.nrodoc,
                    'cuil': afiliado.cuil,
                    'obra_social': afiliado.obra_social.os_nombre
                } for afiliado in afiliados]
                
                return JsonResponse({'resultados': resultados})
            return JsonResponse({'resultados': []})
            
        return super().post(request, *args, **kwargs)
