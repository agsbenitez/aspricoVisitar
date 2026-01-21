import json
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count
from consultas.models import Consulta, PracticaConsulta
from django.utils.timezone import make_aware, datetime
from django.utils import timezone
from datetime import timedelta
from .forms import FiltroEstadisticasForm

class DashboardView(View):
    template_name = 'estadisticas/dashboard.html'

    def get_context_data(self, fecha_inicio, fecha_fin):
        """Método auxiliar para centralizar las consultas"""
        # Ajustamos fecha_fin para que incluya todo el día (hasta las 23:59:59)
        dt_inicio = make_aware(datetime.combine(fecha_inicio, datetime.min.time()))
        dt_fin = make_aware(datetime.combine(fecha_fin, datetime.max.time()))
        #fin_del_dia = timezone.datetime.combine(fecha_fin, timezone.datetime.max.time())
        
        context = {}
        # 1. Totales
        consultas_qs = Consulta.objects.filter(
            tipo='consulta', fecha_emision__range=(dt_inicio, dt_fin)
        )

        context['cant_consultas'] = consultas_qs.filter(tipo='consulta').count()
        context['cant_practicas'] = consultas_qs.filter(tipo='practica').count()

        

        # 2. Ranking Prácticas
        ranking_p_qs = PracticaConsulta.objects.filter(
            consulta__fecha_emision__range=(dt_inicio, dt_fin)
        ).values('practica__descripcion').annotate(total=Count('pk')).order_by('-total')[:10]

        # 3. Ranking Usuarios
        # Intenta esto en views.py para probar:
        ranking_u_qs = (
        consultas_qs.values('usuario__username')
        .annotate(total=Count('pk')) # Probamos con 'id' o 'pk'
        .order_by('-total')
    )

        #ranking_u_qs = consultas_qs.values('usuario__username').annotate(total=Count('pk')).order_by('-total')
        
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