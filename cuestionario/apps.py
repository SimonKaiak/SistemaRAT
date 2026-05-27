"""
apps.py
-------
Configuración de la aplicación Django 'cuestionario'.

CuestionarioConfig:
    default_auto_field → BigAutoField para todas las PKs
                         autogeneradas de la app.
    name               → 'cuestionario'

    ready()            → Se ejecuta cuando Django termina de
                         cargar la app. Importa cuestionario.signals
                         para registrar los signal handlers al inicio,
                         en particular la señal que clona preguntas
                         RAT al crear un nuevo Instrumento.
"""

from django.apps import AppConfig

class CuestionarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cuestionario'

    def ready(self):
        # Esto importa las señales cuando Django arranca
        import cuestionario.signals