from dal import autocomplete
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
import logging
import json
from django.contrib import messages

logger = logging.getLogger(__name__)

from .models import Consulta, Practica, PracticaConsulta
from django.db.models import Prefetch
from .forms import ConsultaForm, ItemPracticaFormSet

from afiliados.models import Afiliado



# Create your views here.
"""
ListaBonosView: Muestra una lista paginada de bonos de consulta con funcionalidad de búsqueda.
"""
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
"""
anular_bono: funcion para anular un bono de consulta mediante una petición POST.
"""
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

""""imprimir_bono: vista para mostrar el bono en formato de impresión."""

@login_required
def imprimir_bono(request, bono_id=None):
    """Vista para mostrar el bono en formato de impresión"""

    qs = (Consulta.objects
          .prefetch_related(
              Prefetch(
                  'practicas_consulta',
                  queryset=PracticaConsulta.objects.select_related('practica')
              )
          ))
    if bono_id:
        bono = get_object_or_404(qs, nro_de_orden=bono_id)
    else:
        # Si no se especifica ID, obtener el último bono generado por el usuario
        bono = qs.filter(usuario=request.user).last()
    
    if not bono:
        messages.error(request, 'No hay bono disponible para imprimir')
        return redirect('consultas:nueva_consulta')
        
    return render(request, 'consultas/bono_consulta_print.html', {
        'consulta': bono,
        'items_practica': bono.practicas_consulta.all(),
    })

def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

"""
NuevaConsultaView:
 Vista para crear una nueva consulta creación.
version refactorizada
 """


class BaseNuevaBonoView(LoginRequiredMixin, CreateView):
    """
    Base común: renderiza el form principal de Consulta
    y agrega 'tipo' al contexto para que la plantilla incluya blocks condicionales.
    """
    form_class = ConsultaForm
    template_name = "consultas/nueva_consulta.html"  # plantilla común
    bono_type = None  # 'consulta' | 'practica'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tipo"] = self.bono_type
        
        if self.request.method == "GET":
            ctx["consulta"] = Consulta(
                fecha_emision=timezone.now(),
                prestador=self.request.user.get_full_name() if self.request.user.is_authenticated else "",
                nro_de_orden=Consulta.objects.count() + 1
            )

        return ctx


class NuevaConsultaView(BaseNuevaBonoView):
    """Vista para crear una nueva consulta médica.
    Extiende la base común y establece bono_type a 'consulta'."""
    bono_type = "consulta"

    
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.usuario = request.user
            obj.save()
            self.object = obj

            if is_ajax(request):
                html_content = render(
                    request,
                    "consultas/bono_consulta.html",
                    {"consulta": self.object, "success": True}
                ).content.decode("utf-8")

                return JsonResponse({
                    "success": True,
                    "html": html_content,
                }, json_dumps_params={"ensure_ascii": False})

            # Si no es AJAX, flujo normal (redirigir o lo que tu base haga)
            return super().post(request, *args, **kwargs)

        # form inválido
        if is_ajax(request):
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        
        
        return self.render_to_response(self.get_context_data(form=form))



    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.usuario = self.request.user   # asigna el usuario autenticado
        obj.tipo = 'consulta'
        obj.save()
        self.object = obj
        return super().form_valid(form)  

class NuevaPracticaView(BaseNuevaBonoView):
    """Vista para crear una nueva consulta con prácticas.
    Extiende la base común y establece bono_type a 'practica'.
    Maneja un formset adicional para las prácticas asociadas."""
    bono_type = "practica"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        formset = ItemPracticaFormSet(request.POST, prefix="items_practica")

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.usuario = request.user
                obj.tipo = 'practica'
                obj.save()
                self.object = obj

                formset.instance = self.object
                formset.save()

            if is_ajax(request):
                items = (
                self.object.practicas_consulta
                .select_related("practica")
                .order_by("id")
            )

                items_json = [
                    {
                        "id": it.pk,
                        "codPractica": it.practica.codPractica,
                        "descripcion": it.practica.descripcion,
                    }
                    for it in items
                ]
                
                html_content = render(
                    request,
                    "consultas/bono_consulta.html",
                    
                    {"consulta": self.object,
                     "tipo": self.bono_type,
                     "items_practica": items_json,
                     "success": True},
                ).content.decode("utf-8")
                
                return JsonResponse({
                    "success": True,
                    "html": html_content,
                    "items_practica": items_json,  # 👈 AÑADIDO
                })
            
            return super().post(request, *args, **kwargs)

        # inválidos…
        if is_ajax(request):
            errors = form.errors
            if formset and formset.errors:
                errors = {"form": form.errors, "formset": formset.non_form_errors()}
                
            return JsonResponse({"success": False, "errors": errors}, status=400)

        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            ctx["formset"] = ItemPracticaFormSet(
                self.request.POST,
                prefix="items_practica",
            )
        else:
            ctx["formset"] = ItemPracticaFormSet(
                prefix="items_practica",
            )
        return ctx

    def form_valid(self, form):
        # Además del form principal, validar/guardar el formset
        ctx = self.get_context_data(form=form)
        formset = ctx["formset"]

        if not formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()          # crea la cabecera Consulta
            formset.instance = self.object     # liga las líneas al padre
            formset.save()                     # crea/actualiza/elimina líneas
        return redirect(self.get_success_url())

"""
NuevaConsultaView:
 Vista para crear una nueva consulta con soporte AJAX para búsquedas y creación.

 Esta Clase pasará a estar decrepita y se implamentará una nnueva clase por ello se la 
 comenta

class NuevaConsultaView(LoginRequiredMixin, CreateView):
    model = Consulta
    form_class = ConsultaForm
    template_name = 'consultas/nueva_consulta.html'
    success_url = reverse_lazy('consultas:nueva_consulta')

    bono_type = None  # 'consulta' o 'practica', se establece en urls.py

    def get_initial(self):
        #Establece valores iniciales para el formulario
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
        #Agrega datos adicionales al contexto
        context = super().get_context_data(**kwargs)
        context['tipo'] = self.bono_type

        # Si es una nueva consulta (GET), creamos un objeto temporal para mostrar
        if self.request.method == 'GET' and self.bono_type == 'consulta':
            context['tipo'] = 'consulta'
            context['consulta'] = Consulta(
                fecha_emision=timezone.now(),
                prestador='',  # Asignar el nombre de usuario del prestador
                nro_de_orden=Consulta.objects.count() + 1  # Número tentativo
            )
        elif self.request.method == 'GET' and self.bono_type == 'practica':
            context['tipo'] = 'practica'
            context['consulta'] = Consulta(
                fecha_emision=timezone.now(),
                prestador='',  # Asignar el nombre de usuario del prestador
                nro_de_orden=Consulta.objects.count() + 1  # Número tentativo
            )
            context['formset'] = ItemPracticaFormSet(
                instance = None,
                prefix='items_practica'
            )
        return context

    def form_valid(self, form):
        #Procesa el formulario válido
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
                    'html': html_content,
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
        #Log de errores cuando el formulario es inválido
        logger.error(f'Errores en el formulario: {form.errors}')
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, content_type='application/json')
        return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        #Maneja las peticiones POST, incluyendo búsquedas AJAX
        #logger.info(f'Método POST recibido - Es AJAX: {request.headers.get("X-Requested-With") == "XMLHttpRequest"}')
        #logger.info(f'Headers recibidos: {request.headers}')
        #logger.info(f'Datos POST recibidos: {request.POST}')

        # Si es una petición AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Verificar si es una búsqueda de afiliados
            if 'buscar_afiliado' in request.POST and not request.headers.get('X-Action'):
                logger.info('Procesando búsqueda de afiliados')
                termino = request.POST.get('buscar_afiliado', '').strip()
                if termino:
                    try:
                        afiliados = Afiliado.objects.select_related('obra_social').filter(
                            Q(nombre__icontains=termino) |
                            Q(nrodoc__icontains=termino) |
                            Q(cuil__icontains=termino)
                        )[:10]  # Limitamos a 10 resultados
                        
                        resultados = [{
                            'id': afiliado.id,
                            'nombre': afiliado.nombre,
                            'nrodoc': afiliado.nrodoc,
                            'cuil': afiliado.cuil,
                            'obra_social': afiliado.obra_social.os_nombre,
                            'monto_coseguro': afiliado.obra_social.monto_coseguro
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
        
        if self.bono_type == 'practica':
            formset = ItemPracticaFormSet(
                request.POST,
                instance=None,
                prefix='items_practica'
            )
        else:
            formset = None
        # Si no es AJAX, procesar normalmente
        return super().post(request, *args, **kwargs)
"""

"""Vista para autocompletar prácticas
Esta vista utiliza el paquete django-autocomplete-light para proporcionar
un autocompletado de prácticas basado en el código o la descripción.
El usuario puede buscar prácticas y seleccionar una de la lista desplegable."""
class PracticaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Practica.objects.all()
        print(f"QuerySet inicial: {qs.query}")
        if self.q:
            qs = qs.filter(
                Q(codPractica__icontains=self.q) |
                Q(descripcion__icontains=self.q)
            )
        return qs
    
def search_afiliados(request):
    """
    GET /consultas/ajax/afiliados/?q=texto
    Devuelve lista simple para autocompletar/buscar afiliados.
    """
    print("Atiende la buscqueda de afiliados via ajax")
    if request.method != "GET":
        return HttpResponseBadRequest("Método no permitido")

    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})

    # Ajustá los campos de filtro a tu modelo Afiliado
    afiliados = Afiliado.objects.select_related('obra_social').filter(
                            Q(nombre__icontains=q) |
                            Q(nrodoc__icontains=q) |
                            Q(cuil__icontains=q)
                        )[:10]  # Limitamos a 10 resultados

    resultados = [{
                            'id': afiliado.id,
                            'nombre': afiliado.nombre,
                            'nrodoc': afiliado.nrodoc,
                            'cuil': afiliado.cuil,
                            'obra_social': afiliado.obra_social.os_nombre,
                            'monto_coseguro': afiliado.obra_social.monto_coseguro
                        } for afiliado in afiliados]
    
    return JsonResponse({"results": resultados})

def search_practicas(request):
    q = (request.GET.get('q') or '').strip()
    qs = Practica.objects.all()
    if q:
        qs = qs.filter(Q(codPractica__icontains=q) | Q(descripcion__icontains=q))
    qs = qs.order_by('codPractica')[:50]  # limita resultados
    data = [{"id": p.id, "codPractica": p.codPractica, "descripcion": p.descripcion} for p in qs]
    return JsonResponse({"results": data})