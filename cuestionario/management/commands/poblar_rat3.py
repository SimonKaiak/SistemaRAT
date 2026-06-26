from django.core.management.base import BaseCommand
from cuestionario.models import Instrumento, RATPlantillaPregunta


PREGUNTAS_RAT3 = [
    {'orden': 1, 'enunciado': '¿Qué tipo de datos personales se recopilan en este proceso?', 'tipo': 'texto'},
    {'orden': 2, 'enunciado': '¿Se comparten estos datos con terceros?', 'tipo': 'sino'},
    {'orden': 3, 'enunciado': '¿Cuál es el nivel de riesgo asociado al tratamiento de estos datos?', 'tipo': 'escala'},
]


class Command(BaseCommand):
    help = 'Crea el Instrumento RAT 3 de prueba (seguro para re-ejecutar)'

    def handle(self, *args, **kwargs):
        self.stdout.write('🔧 Creando Instrumento RAT 3...')

        instrumento, creado = Instrumento.objects.get_or_create(
            nombre_instrumento='RAT 3',
            defaults={
                'descripcion': 'Instrumento RAT 3 de prueba.',
                'activo': True,
            },
        )

        if creado:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Instrumento creado → id={instrumento.pk}'))
        else:
            self.stdout.write(f'  ℹ️  Instrumento ya existía → id={instrumento.pk}')

        self.stdout.write('🔧 Cargando preguntas plantilla...')
        creadas = 0
        existentes = 0

        for pregunta in PREGUNTAS_RAT3:
            obj, nuevo = RATPlantillaPregunta.objects.get_or_create(
                instrumento=instrumento,
                enunciado=pregunta['enunciado'],
                defaults={
                    'orden': pregunta['orden'],
                    'tipo': pregunta['tipo'],
                },
            )
            if nuevo:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ [{obj.orden}] {obj.enunciado[:60]}'))
            else:
                obj.orden = pregunta['orden']
                obj.tipo = pregunta['tipo']
                obj.save()
                existentes += 1
                self.stdout.write(f'  ℹ️  [{obj.orden}] actualizado')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✅ Listo. Preguntas creadas: {creadas} | Ya existían: {existentes}'
        ))