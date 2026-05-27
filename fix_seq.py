"""
fix_seq.py
----------
Script de utilidad para corregir la secuencia de la PK de la
tabla TRABAJADOR en PostgreSQL.

Problema que resuelve:
    Cuando los datos se insertan manualmente con IDs explícitos
    (via SQL directo o bulk_create), la secuencia SERIAL de
    PostgreSQL no se actualiza automáticamente. Esto causa errores
    de duplicate key al intentar crear nuevos registros desde
    Django, ya que la secuencia sigue desde 1 aunque ya existan
    registros con IDs mayores.

Solución:
    Ejecuta setval() con el MAX(id_trabajador) actual para
    sincronizar la secuencia con los datos existentes.

Uso:
    python fix_seq.py

    Ejecutar desde la raíz del proyecto después de cargar datos
    manualmente en la tabla TRABAJADOR.
"""

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