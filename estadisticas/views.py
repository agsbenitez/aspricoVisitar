# 1. Standard Library Imports (Librerías nativas de Python)
import csv
import json

# 2. Related Third Party Imports (Librerías de Django / Externas)
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.utils import timezone
from django.utils.timezone import make_aware, datetime
from django.shortcuts import render
from django.views.generic import View

# 3. Local Application Imports (Tus modelos y formularios)
from .forms import FiltroEstadisticasForm
from consultas.models import Consulta, PracticaConsulta

def es_administrador(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def obtener_rango_fechas_aware(fecha_inicio, fecha_fin):
    """
    Recibe objetos date y devuelve objetos datetime 'aware' 
    ajustados al inicio y fin del día en la zona horaria local.
    """
    # Combinamos la fecha con la hora mínima (00:00:00) y máxima (23:59:59)
    dt_inicio = make_aware(datetime.combine(fecha_inicio, datetime.min.time()))
    dt_fin = make_aware(datetime.combine(fecha_fin, datetime.max.time()))
    
    return dt_inicio, dt_fin

@login_required
def exportar_consultas_csv(request):
    # 1. Obtenemos las fechas de la URL (o usamos las del mes actual por defecto)
    inicio_str = request.GET.get('inicio')
    fin_str = request.GET.get('fin')
    
    # Lógica de fechas (reutilizando tu configuración de Buenos Aires)
    if inicio_str and fin_str:
        fecha_inicio = datetime.strptime(inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fin_str, '%Y-%m-%d').date()
    else:
        hoy = datetime.now().date()
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy

    dt_inicio, dt_fin = obtener_rango_fechas_aware(fecha_inicio, fecha_fin)

    # 2. Preparamos el Response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_detallado_{inicio_str}.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')

    # Agregamos columnas de Cód. Práctica, Descripción y Cantidad
    writer.writerow([
        'Nro Orden', 'Fecha Emisión', 'Tipo', 'Afiliado', 
        'Obra Social', 'Usuario', 'Cód. Práctica', 
        'Descripción Práctica', 'Cantidad', 'Diagnóstico'
    ])

    # Optimizamos la consulta con prefetch_related para las prácticas
    consultas = Consulta.objects.filter(
        fecha_emision__range=(dt_inicio, dt_fin)
    ).select_related('afiliado', 'obra_social', 'usuario').prefetch_related('practicas_consulta__practica')

    for c in consultas:
        detalles = c.practicas_consulta.all()
        
        if detalles.exists():
            # Si tiene prácticas, creamos una fila por cada una
            for detalle in detalles:
                writer.writerow([
                    c.nro_de_orden,
                    c.fecha_emision.strftime('%d/%m/%Y %H:%M'),
                    c.get_tipo_display(),
                    c.afiliado.nombre,
                    c.obra_social.os_nombre,
                    c.usuario.username,
                    detalle.practica.codPractica, # Código de la práctica
                    detalle.practica.descripcion,  # Nombre de la práctica
                    detalle.cantidad,              # Cantidad solicitada
                    c.diagnostico
                ])
        else:
            # Si es una consulta médica simple (sin prácticas detalladas)
            writer.writerow([
                c.nro_de_orden,
                c.fecha_emision.strftime('%d/%m/%Y %H:%M'),
                c.get_tipo_display(),
                c.afiliado.nombre,
                c.obra_social.os_nombre,
                c.usuario.username,
                'N/A', 'CONSULTA MÉDICA', 1,
                c.diagnostico
            ])

    return response

class DashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'estadisticas/dashboard.html'

    # Esta función determina si el usuario tiene permiso
    def test_func(self):
        # Retorna True si es superusuario o staff
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_context_data(self, fecha_inicio, fecha_fin):
        """Método auxiliar para centralizar las consultas"""
        # Ajustamos fecha_fin para que incluya todo el día (hasta las 23:59:59)
        dt_inicio, dt_fin = obtener_rango_fechas_aware(fecha_inicio, fecha_fin)
        #fin_del_dia = timezone.datetime.combine(fecha_fin, timezone.datetime.max.time())
        
        context = {}
        # 1. Totales
        consultas_qs = Consulta.objects.filter(
            fecha_emision__range=(dt_inicio, dt_fin)
        )

        context['cant_consultas'] = consultas_qs.filter(tipo='consulta').count()
        context['cant_practicas'] = consultas_qs.filter(tipo='practica').count()
        context['cant_total'] = context['cant_consultas'] + context['cant_practicas']
        
        # 2. Ranking Prácticas
        ranking_p_qs = PracticaConsulta.objects.filter(
            consulta__fecha_emision__range=(dt_inicio, dt_fin)
        ).values('practica__descripcion').annotate(total=Count('pk')).order_by('-total')[:10]

        # 3. Ranking Usuarios
        # Intenta esto en views.py para probar:
        ranking_u_qs = (
        consultas_qs.values('usuario__username')
        .annotate(total=Count('pk')) 
        .order_by('-total')
        )

        #4. Ranking de Prácticas para la tabla
        ranking_practicas_qs = (
            PracticaConsulta.objects.filter(consulta__in=consultas_qs)
            .values('practica__descripcion', 'practica__codPractica')
            .annotate(total=Count('id'))
            .order_by('-total')[:10] # Top 10
        )
    
        context['ranking_practicas_tabla'] = ranking_practicas_qs

        # --- CONVERSIÓN A JSON PARA JS ---
        context['labels_practicas'] = json.dumps([item['practica__descripcion'] for item in ranking_p_qs])
        context['data_practicas'] = json.dumps([item['total'] for item in ranking_p_qs])

        context['labels_usuarios'] = json.dumps([item['usuario__username'] for item in ranking_u_qs])
        context['data_usuarios'] = json.dumps([item['total'] for item in ranking_u_qs])
        
        context['fecha_inicio'] = dt_inicio
        context['fecha_fin'] = dt_fin

        print(f"DEBUG: Total de consultas en este rango: {consultas_qs.count()}")
        print(f"DEBUG: Consultas con usuario asignado: {consultas_qs.exclude(usuario=None).count()}")
        return context

    def get(self, request):
        # Rango inicial: desde el primer día del mes actual
        hoy = timezone.now().date()
        inicio = hoy.replace(day=1)
        
        form = FiltroEstadisticasForm(initial={'fecha_inicio': inicio, 'fecha_fin': hoy})
        context = self.get_context_data(inicio, hoy)
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request):
        form = FiltroEstadisticasForm(request.POST)
        if form.is_valid():
            inicio = form.cleaned_data['fecha_inicio']
            fin = form.cleaned_data['fecha_fin']
            context = self.get_context_data(inicio, fin)
        else:
            # Si hay error, volvemos a valores por defecto
            hoy = timezone.now().date()
            inicio = hoy.replace(day=1)
            context = self.get_context_data(inicio, hoy)
        
        context['form'] = form
        return render(request, self.template_name, context)