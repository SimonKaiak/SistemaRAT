"""
management/commands/poblar_rat_kickoff.py
------------------------------------------
Comando de gestión de Django para crear el Instrumento Kick Off
y sus preguntas plantilla (RAT V1) según el boceto de Ignacio.

Uso:
    python manage.py poblar_rat_kickoff

Comportamiento:
- Crea el Instrumento 'Kick Off' si no existe (get_or_create, seguro
  para re-ejecutar múltiples veces sin duplicar datos).
- Crea las 7 entradas en RATPlantillaPregunta asociadas al instrumento,
  usando get_or_create por (instrumento, orden) para evitar duplicados.
- Tipos usados:
    texto  → texto libre
    sino   → Sí / No  (se guarda 1 cuando la respuesta es Sí)
    escala → 5 alternativas (escala 1-5)

Preguntas del Instrumento Kick Off (boceto Ignacio, RAT V1):
    0  Presentación — qué se entiende por datos personales  (texto, intro)
    1  ¿Ud. conoce la Ley de Datos Personales?              (sino)
    2  ¿Como parte de sus tareas laborales regulares, Ud.
       usa, modifica o crea archivos con datos personales?  (sino)
    3  ¿Qué tan familiarizado(a) está con los principios
       éticos relacionados con el uso y tratamiento de
       datos personales en su organización?                 (escala)
    4  ¿Con qué frecuencia recibe formación o
       sensibilización sobre ética y protección de datos?   (texto)
    5  ¿Cuál considera que es el principal riesgo ético
       asociado al tratamiento de datos personales en
       su organización?                                     (texto)
    6  ¿Qué aspecto considera más relevante de fortalecer
       en su organización en materia de ética y
       protección de datos?                                 (texto)
    7  Fuente de la cual provienen los datos                (texto)
"""

from django.core.management.base import BaseCommand
from cuestionario.models import Instrumento, RATPlantillaPregunta


PREGUNTAS = [
    {
        'orden': 0,
        'enunciado': (
            'Presentación: ¿Qué se entiende por datos personales?\n\n'
            'Los datos personales son toda información que permite identificar '
            'o hacer identificable a una persona natural, como nombre, RUT, '
            'dirección, correo electrónico, entre otros. Su tratamiento está '
            'regulado por la Ley de Datos Personales con el fin de proteger '
            'la privacidad y los derechos de las personas.'
        ),
        'tipo': 'texto',
    },
    {
        'orden': 1,
        'enunciado': '¿Ud. conoce la Ley de Datos Personales?',
        'tipo': 'sino',
    },
    {
        'orden': 2,
        'enunciado': (
            'Como parte de sus tareas laborales regulares, ¿Ud. usa, modifica '
            'o crea archivos con datos personales?'
        ),
        'tipo': 'sino',
    },
    {
        'orden': 3,
        'enunciado': (
            '¿Qué tan familiarizado(a) está con los principios éticos '
            'relacionados con el uso y tratamiento de datos personales '
            'en su organización?'
        ),
        'tipo': 'escala',
    },
    {
        'orden': 4,
        'enunciado': (
            '¿Con qué frecuencia recibe formación o sensibilización sobre '
            'ética y protección de datos?'
        ),
        'tipo': 'texto',
    },
    {
        'orden': 5,
        'enunciado': (
            '¿Cuál considera que es el principal riesgo ético asociado al '
            'tratamiento de datos personales en su organización?'
        ),
        'tipo': 'texto',
    },
    {
        'orden': 6,
        'enunciado': (
            '¿Qué aspecto considera más relevante de fortalecer en su '
            'organización en materia de ética y protección de datos?'
        ),
        'tipo': 'texto',
    },
    {
        'orden': 7,
        'enunciado': 'Fuente de la cual provienen los datos.',
        'tipo': 'texto',
    },
]


class Command(BaseCommand):
    help = 'Crea el Instrumento Kick Off y sus preguntas RAT V1 (seguro para re-ejecutar)'

    def handle(self, *args, **kwargs):
        self.stdout.write('🔧 Creando Instrumento Kick Off...')

        instrumento, creado = Instrumento.objects.get_or_create(
            nombre_instrumento='Kick Off',
            defaults={
                'descripcion': (
                    'Instrumento de diagnóstico inicial sobre conocimiento y '
                    'manejo de datos personales en la organización (RAT V1).'
                ),
                'activo': True,
            },
        )

        if creado:
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ Instrumento creado → id={instrumento.pk}'
            ))
        else:
            self.stdout.write(
                f'  ℹ️  Instrumento ya existía → id={instrumento.pk}'
            )

        self.stdout.write('🔧 Cargando preguntas plantilla...')
        creadas = 0
        existentes = 0

        for pregunta in PREGUNTAS:
            obj, nuevo = RATPlantillaPregunta.objects.get_or_create(
                instrumento=instrumento,
                orden=pregunta['orden'],
                defaults={
                    'enunciado': pregunta['enunciado'],
                    'tipo': pregunta['tipo'],
                },
            )
            if nuevo:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ [{obj.orden}] {obj.enunciado[:60]}...'
                ))
            else:
                existentes += 1
                self.stdout.write(
                    f'  ℹ️  [{obj.orden}] ya existe — sin cambios'
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✅ Listo. Preguntas creadas: {creadas} | Ya existían: {existentes}'
        ))