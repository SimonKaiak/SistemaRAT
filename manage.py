#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

"""
manage.py
---------
Punto de entrada de la línea de comandos de Django.
Generado automáticamente por Django.

Configura DJANGO_SETTINGS_MODULE a 'Sistema_Mohala.settings'
y delega la ejecución a django.core.management.

Uso:
    python manage.py <comando>

Comandos más usados en el proyecto:
    migrate           → aplica migraciones.
    crear_admin       → crea el superusuario desde variables de entorno.
    poblar_usuarios   → vincula usuarios Django a trabajadores.
    crear_tablas      → crea tablas managed=False en PostgreSQL.
    runserver         → inicia el servidor de desarrollo.
"""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sistema_Mohala.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
