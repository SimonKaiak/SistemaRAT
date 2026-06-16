"""
management/commands/poblar_empresas.py
----------------------------------------
Carga los datos de Mohala y Permify ejecutando los .sql ya incluidos
en el repositorio. Seguro para re-ejecutar: si la Empresa 1 ya existe,
no hace nada.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Carga los datos de Mohala y Permify desde los .sql del repo (solo si no existen)'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute('SELECT EXISTS (SELECT 1 FROM "EMPRESA" WHERE id_empresa = 1)')
            ya_existe = cursor.fetchone()[0]

        if ya_existe:
            self.stdout.write(self.style.WARNING(
                '⚠️  La Empresa 1 ya existe. Se omite la carga de datos.'
            ))
            return

        archivos = [
            settings.BASE_DIR / 'poblacion_empresa_mohala.sql',
            settings.BASE_DIR / 'poblacion_empresa_permify.sql',
        ]

        with connection.cursor() as cursor:
            for archivo in archivos:
                self.stdout.write(f'🔧 Ejecutando {archivo.name}...')
                sql = archivo.read_text(encoding='utf-8')
                cursor.execute(sql)
                self.stdout.write(self.style.SUCCESS(f'✅ {archivo.name} ejecutado.'))

            self.stdout.write('🔧 Corrigiendo secuencias...')
            cursor.execute("""
                SELECT setval(pg_get_serial_sequence('"EMPRESA"', 'id_empresa'), COALESCE((SELECT MAX(id_empresa) FROM "EMPRESA"), 1));
                SELECT setval(pg_get_serial_sequence('"DEPARTAMENTO"', 'id_departamento'), COALESCE((SELECT MAX(id_departamento) FROM "DEPARTAMENTO"), 1));
                SELECT setval(pg_get_serial_sequence('"NIVEL_JERARQUICO"', 'id_nivel_jerarquico'), COALESCE((SELECT MAX(id_nivel_jerarquico) FROM "NIVEL_JERARQUICO"), 1));
                SELECT setval(pg_get_serial_sequence('"ESCALA"', 'id_escala'), COALESCE((SELECT MAX(id_escala) FROM "ESCALA"), 1));
                SELECT setval(pg_get_serial_sequence('"DIMENSION"', 'id_dimension'), COALESCE((SELECT MAX(id_dimension) FROM "DIMENSION"), 1));
                SELECT setval(pg_get_serial_sequence('"COMPETENCIA"', 'id_competencia'), COALESCE((SELECT MAX(id_competencia) FROM "COMPETENCIA"), 1));
                SELECT setval(pg_get_serial_sequence('"CARGO"', 'id_cargo'), COALESCE((SELECT MAX(id_cargo) FROM "CARGO"), 1));
                SELECT setval(pg_get_serial_sequence('"TEXTOS_EVALUACION"', 'id_textos_evaluacion'), COALESCE((SELECT MAX(id_textos_evaluacion) FROM "TEXTOS_EVALUACION"), 1));
                SELECT setval(pg_get_serial_sequence('"CODIGO_EVALUACION"', 'id_codigo_evaluacion'), COALESCE((SELECT MAX(id_codigo_evaluacion) FROM "CODIGO_EVALUACION"), 1));
                SELECT setval(pg_get_serial_sequence('"TRABAJADOR"', 'id_trabajador'), COALESCE((SELECT MAX(id_trabajador) FROM "TRABAJADOR"), 1));
            """)

        self.stdout.write(self.style.SUCCESS('✅ Empresas cargadas y secuencias corregidas.'))