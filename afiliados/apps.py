from django.apps import AppConfig


class AfiliadosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'afiliados'

    def ready(self):
        # Importamos los signals aquí para que se registren al iniciar el servidor
        import afiliados.signals
