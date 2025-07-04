from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
import logging
import json
from django.contrib import messages

logger = logging.getLogger(__name__)

from .models import Consulta
from .forms import ConsultaForm
from afiliados.models import Afiliado

# Create your views here.

class ListaBonosView(LoginRequiredMixin, ListView):
    model = Consulta
    template_name = 'consultas/lista_bonos.html'
    context_object_name = 'consultas'
    paginate_by = 10

    def get_queryset(self):
        queryset = Consulta.objects.all().order_by('-fecha_emision')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(afiliado__nombre__icontains=q) |
                Q(afiliado__nrodoc__icontains=q) |
                Q(afiliado__cuil__icontains=q)
            )
        return queryset

@login_required
def anular_bono(request, bono_id):
    if request.method == 'POST':
        try:
            bono = get_object_or_404(Consulta, nro_de_orden=bono_id)
            if not bono.activo:
                return JsonResponse({
                    'success': False,
                    'error': 'El bono ya está anulado'
                })
            
            bono.activo = False
            bono.save()
            
            return JsonResponse({
                'success': True
            })
        except Exception as e:
            logger.error(f'Error al anular bono {bono_id}: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })

@login_required
def imprimir_bono(request, bono_id=None):
    """Vista para mostrar el bono en formato de impresión"""
    if bono_id:
        bono = get_object_or_404(Consulta, nro_de_orden=bono_id)
    else:
        # Si no se especifica ID, obtener el último bono generado por el usuario
        bono = Consulta.objects.filter(usuario=request.user).last()
    
    if not bono:
        messages.error(request, 'No hay bono disponible para imprimir')
        return redirect('consultas:nueva_consulta')
        
    return render(request, 'consultas/bono_consulta_print.html', {
        'consulta': bono
    })

class NuevaConsultaView(LoginRequiredMixin, CreateView):
    model = Consulta
    form_class = ConsultaForm
    template_name = 'consultas/nueva_consulta.html'
    success_url = reverse_lazy('consultas:nueva_consulta')

    bono_type = 'consulta'

    def get_initial(self):
        """Establece valores iniciales para el formulario"""
        initial = super().get_initial()
        # se anula esta linea paara tomarl el valore del campo he imprimirlo 
        initial['prestador'] = ''
        initial['fecha_emision'] = timezone.now()
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault('initial', {})['tipo'] = self.bono_type
        return kwargs

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto"""
        context = super().get_context_data(**kwargs)
        # Si es una nueva consulta (GET), creamos un objeto temporal para mostrar
        if self.request.method == 'GET':
            context['consulta'] = Consulta(
                fecha_emision=timezone.now(),
                prestador='',  # Asignar el nombre de usuario del prestador
                nro_de_orden=Consulta.objects.count() + 1  # Número tentativo
            )
        return context

    def form_valid(self, form):
        """Procesa el formulario válido"""
        try:
            form.instance.tipo = self.bono_type
            logger.info('Iniciando form_valid en NuevaConsultaView')
            
            # Asignar datos básicos
            form.instance.usuario = self.request.user
            form.instance.fecha_emision = timezone.now()
            
            # Log de los datos del formulario
            logger.info(f'Datos del formulario: {form.cleaned_data}')
            
            # Guardar la instancia
            self.object = form.save()
            logger.info(f'Consulta creada con ID: {self.object.nro_de_orden}')
            
            # Si es una petición AJAX, devolver HTML renderizado
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Renderizar el template con los datos actualizados
                html_content = render(self.request, 'consultas/bono_consulta.html', {
                    'consulta': self.object,
                    'success': True
                }).content.decode('utf-8')
                
                return JsonResponse({
                    'success': True,
                    'html': html_content
                }, json_dumps_params={'ensure_ascii': False})
            
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f'Error en form_valid: {str(e)}')
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                error_data = {
                    'success': False,
                    'errors': str(e)
                }
                logger.error(f'Enviando respuesta de error: {error_data}')
                return JsonResponse(
                    error_data,
                    content_type='application/json',
                    json_dumps_params={'ensure_ascii': False}
                )
            raise

    def form_invalid(self, form):
        """Log de errores cuando el formulario es inválido"""
        logger.error(f'Errores en el formulario: {form.errors}')
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, content_type='application/json')
        return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        """Maneja las peticiones POST, incluyendo búsquedas AJAX"""
        logger.info(f'Método POST recibido - Es AJAX: {request.headers.get("X-Requested-With") == "XMLHttpRequest"}')
        logger.info(f'Headers recibidos: {request.headers}')
        logger.info(f'Datos POST recibidos: {request.POST}')

        # Si es una petición AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Verificar si es una búsqueda de afiliados
            if 'buscar_afiliado' in request.POST and not request.headers.get('X-Action'):
                logger.info('Procesando búsqueda de afiliados')
                termino = request.POST.get('buscar_afiliado', '').strip()
                if termino:
                    try:
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
                        
                        return JsonResponse({'resultados': resultados}, content_type='application/json')
                    except Exception as e:
                        logger.error(f'Error en búsqueda de afiliados: {str(e)}')
                        return JsonResponse({
                            'success': False,
                            'error': str(e)
                        }, content_type='application/json')
                        
                return JsonResponse({'resultados': []}, content_type='application/json')
            
            # Si es una creación de consulta (tiene X-Action o tiene afiliado_id)
            elif request.headers.get('X-Action') == 'create_consulta' or 'afiliado_id' in request.POST:
                logger.info('Procesando creación de consulta')
                return super().post(request, *args, **kwargs)
            
            # Si no es ninguna de las anteriores, es un error
            else:
                logger.error('Petición AJAX no reconocida')
                return JsonResponse({
                    'success': False,
                    'errors': 'Tipo de petición no reconocida'
                }, content_type='application/json')
        
        # Si no es AJAX, procesar normalmente
        return super().post(request, *args, **kwargs)
