import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sistema_Mohala.settings')
django.setup()

from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT setval(
            pg_get_serial_sequence('"TRABAJADOR"', 'id_trabajador'),
            MAX(id_trabajador)
        ) FROM "TRABAJADOR";
    """)
    print('OK:', cursor.fetchone())