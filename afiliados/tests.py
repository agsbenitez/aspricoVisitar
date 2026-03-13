from django.test import TestCase
from django.utils import timezone
from .models import Afiliado, ObraSocial
import pandas as pd
from io import BytesIO
# Importamos la lógica de tu vista o el helper si lo separaste
# Aquí asumiremos que probamos el comportamiento de los modelos tras la lógica

class SincronizacionAfiliadosTest(TestCase):
    
    def setUp(self):
        """Configuración inicial: Un afiliado y una OS que fueron dados de baja"""
        self.fecha_ayer = timezone.now().date()
        
        # 1. Creamos la OS inactiva
        self.os_inactiva = ObraSocial.objects.create(
            os_id="100",
            os_nombre="Obra Social Test",
            activa=False,
            fecha_baja=self.fecha_ayer
        )
        
        # 2. Creamos el Afiliado inactivo vinculado a esa OS
        self.afiliado_inactivo = Afiliado.objects.create(
            nrodoc="12345678",
            nombre="Juan Pueblo",
            obra_social=self.os_inactiva,
            baja=True,
            fecha_baja="",
            # Completar con campos mínimos requeridos por tu modelo
        )

    def test_resurreccion_afiliado_y_os(self):
        """
        Caso: El afiliado y su OS estaban de baja, pero reaparecen en el nuevo Excel.
        Resultado esperado: Ambos deben quedar activos y sin fecha de baja.
        """
        # SIMULACIÓN: Los datos que vendrían en el Excel
        os_id_excel = "100"
        nrodoc_excel = "12345678"
        
        # --- LÓGICA A PROBAR (la que incluiremos en form_valid) ---
        
        # 1. Procesar OS
        os_obj, _ = ObraSocial.objects.update_or_create(
            os_id=os_id_excel,
            defaults={'activa': True, 'fecha_baja': None}
        )
        
        # 2. Procesar Afiliado
        afiliado = Afiliado.objects.get(nrodoc=nrodoc_excel)
        afiliado.obra_social = os_obj
        afiliado.baja = False
        afiliado.fecha_baja = None
        afiliado.save()
        
        # --- VERIFICACIONES (Assertions) ---
        
        # Recargamos de la base de datos
        self.os_inactiva.refresh_from_db()
        self.afiliado_inactivo.refresh_from_db()
        
        # Verificamos que la OS ahora está activa
        self.assertTrue(self.os_inactiva.activa)
        self.assertIsNone(self.os_inactiva.fecha_baja)
        
        # Verificamos que el Afiliado ahora está activo
        self.assertFalse(self.afiliado_inactivo.baja)
        self.assertIsNone(self.afiliado_inactivo.fecha_baja)
        self.assertEqual(self.afiliado_inactivo.obra_social.os_id, "100")

    def test_inactivacion_por_ausencia(self):
        """
        Caso: Una OS está activa en BD pero no se menciona en los IDs del Excel.
        """
        # IDs que "vimos" en el excel (la 100 no está)
        ids_vistos_en_excel = ["200", "300"]
        
        # Ponemos la OS 100 como activa primero
        self.os_inactiva.activa = True
        self.os_inactiva.save()
        
        # Ejecutamos lógica de limpieza
        ObraSocial.objects.exclude(os_id__in=ids_vistos_en_excel).update(
            activa=False, 
            fecha_baja=timezone.now().date()
        )
        
        self.os_inactiva.refresh_from_db()
        self.assertFalse(self.os_inactiva.activa)
        self.assertIsNotNone(self.os_inactiva.fecha_baja)