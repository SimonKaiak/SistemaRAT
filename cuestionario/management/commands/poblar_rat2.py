from django.core.management.base import BaseCommand
from cuestionario.models import Instrumento, RATPlantillaPregunta


PREGUNTAS_RAT2 = [
    {'orden': 1,  'enunciado': 'Actividad de tratamiento',                                                                 'tipo': 'select_actividad'},
    {'orden': 2,  'enunciado': 'Responsable o encargado',                                                                  'tipo': 'listado_usuario_unico'},
    {'orden': 3,  'enunciado': 'Categoría, clases o tipos de datos que se tratan',                                         'tipo': 'select_categorias'},
    {'orden': 4,  'enunciado': 'Formato del archivo de datos',                                                             'tipo': 'select_formato'},
    {'orden': 5,  'enunciado': 'Descripción del universo de los titulares de los datos personales',                        'tipo': 'texto'},
    {'orden': 6,  'enunciado': 'Finalidad de tratamiento',                                                                 'tipo': 'texto'},
    {'orden': 7,  'enunciado': 'Base de legitimidad del tratamiento',                                                      'tipo': 'select_base_legitimidad'},
    {'orden': 8,  'enunciado': 'Destinatarios a los que se prevé comunicar o ceder los datos, incluida la transferencia internacional de datos', 'tipo': 'listado_usuarios'},
    {'orden': 9,  'enunciado': 'Período de conservación',                                                                  'tipo': 'periodo'},
    {'orden': 10, 'enunciado': 'Fuente de la cual provienen los datos',                                                    'tipo': 'texto'},
]


class Command(BaseCommand):
    help = 'Crea el Instrumento RAT 2 y sus preguntas plantilla (seguro para re-ejecutar)'

    def handle(self, *args, **kwargs):
        self.stdout.write('🔧 Creando Instrumento RAT 2...')

        instrumento, creado = Instrumento.objects.get_or_create(
            nombre_instrumento='RAT 2',
            defaults={
                'descripcion': 'Registro de Actividad de Tratamiento (RAT 2).',
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

        for pregunta in PREGUNTAS_RAT2:
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
                self.stdout.write(f'  ℹ️  [{obj.orden}] actualizado — orden y tipo corregidos')

        # Corregir orden en RATPreguntas existentes para todas las empresas
        from cuestionario.models import RATPreguntas, InstrumentoEmpresa
        for ie in InstrumentoEmpresa.objects.filter(instrumento=instrumento):
            for pregunta in PREGUNTAS_RAT2:
                RATPreguntas.objects.filter(
                    instrumento_empresa=ie,
                    actividad_tratamiento__icontains=pregunta['enunciado'][:30]
                ).update(orden=pregunta['orden'], tipo=pregunta['tipo'])
        self.stdout.write(self.style.SUCCESS('✅ Órdenes corregidos en RATPreguntas existentes'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✅ Listo. Preguntas creadas: {creadas} | Ya existían: {existentes}'
        ))