"""cuestionario/signals.py

Señales del sistema:
  1. crear_usuario_automatico  — crea User de Django al crear un Trabajador
  2. clonar_preguntas_rat      — al habilitar un InstrumentoEmpresa de tipo RAT,
                                  clona las preguntas base (RATPlantillaPregunta)
                                  a RATPreguntas para esa empresa.
"""
"""
signals.py
----------
Señales Django del sistema. Se importa desde apps.py (ready())
para registrar los handlers al iniciar la aplicación.

Helper:
    get_password_por_empresa(trabajador)
        Retorna la contraseña por defecto según la empresa del
        trabajador. Empresas conocidas:
            1 (Mohala)  → 'Mohala2026'
            2 (Permify) → 'Permify2026'
            otras       → 'DefaultPass2026'

Señal 1: crear_usuario_automatico
    Receptor: post_save en Trabajador.
    Condición: solo si es creación (created=True) y no tiene
               user asignado.
    Acción: crea un User de Django con username=email y
            contraseña según get_password_por_empresa, y lo
            vincula al Trabajador.

    Nota: existe una versión similar en models.py con contraseña
    fija 'Mohala2026'. Esta versión en signals.py asigna la
    contraseña correcta por empresa y es la que está activa
    gracias a la importación en apps.py ready().

Señal 2: clonar_preguntas_rat
    Receptor: post_save en InstrumentoEmpresa.
    Condición: solo si es creación (created=True), el instrumento
               tiene plantillas base (RATPlantillaPregunta) y aún
               no hay preguntas en ese InstrumentoEmpresa.
    Acción: clona cada RATPlantillaPregunta del instrumento como
            RATPreguntas asociada al InstrumentoEmpresa creado,
            mapeando enunciado → actividad_tratamiento con valores
            por defecto en los campos restantes.
    Responsable: primer coordinador de la empresa, o primer
                 trabajador disponible. Si no hay trabajadores
                 registrados aún, no clona (se crean manualmente).
    Usa bulk_create para eficiencia.
    Import de RATPlantillaPregunta y RATPreguntas dentro de la
    función para evitar importación circular al arrancar Django.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from cuestionario.models import Trabajador, InstrumentoEmpresa


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_password_por_empresa(trabajador):
    passwords = {
        1: 'Mohala2026',
        2: 'Permify2026',
    }
    return passwords.get(trabajador.empresa_id, 'DefaultPass2026')


# ─── Señal 1: crear usuario automático ────────────────────────────────────────

@receiver(post_save, sender=Trabajador)
def crear_usuario_automatico(sender, instance, created, **kwargs):
    if created and not instance.user:
        password = get_password_por_empresa(instance)
        nuevo_user = User.objects.create_user(
            username=instance.email,
            email=instance.email,
            password=password,
        )
        instance.user = nuevo_user
        instance.save()


# ─── Señal 2: clonar preguntas RAT al habilitar instrumento ───────────────────

@receiver(post_save, sender=InstrumentoEmpresa)
def clonar_preguntas_rat(sender, instance, created, **kwargs):
    """
    Cuando se crea un InstrumentoEmpresa cuyo instrumento es de tipo RAT,
    copia las preguntas base (RATPlantillaPregunta) a RATPreguntas
    asociadas a este InstrumentoEmpresa.

    Solo clona si:
    - Es un registro nuevo (created=True)
    - El instrumento tiene preguntas base definidas
    - Aún no hay preguntas en este InstrumentoEmpresa (evita duplicados)
    """
    if not created:
        return

    # Import aquí para evitar circular import al arrancar Django
    from cuestionario.models import RATPlantillaPregunta, RATPreguntas

    instrumento = instance.instrumento

    # Solo actúa si hay plantilla para este instrumento
    plantillas = RATPlantillaPregunta.objects.filter(instrumento=instrumento).order_by('orden')
    if not plantillas.exists():
        return

    # Evitar duplicados si por algún motivo se llama dos veces
    if RATPreguntas.objects.filter(instrumento_empresa=instance).exists():
        return

    # Buscar un responsable por defecto (el primer coordinador de la empresa)
    responsable = (
        Trabajador.objects.filter(empresa=instance.empresa, es_coordinador=True).first()
        or Trabajador.objects.filter(empresa=instance.empresa).first()
    )
    if not responsable:
        # Sin trabajadores aún — las preguntas se pueden crear después manualmente
        return

    preguntas_a_crear = []
    for plantilla in plantillas:
        preguntas_a_crear.append(RATPreguntas(
            instrumento_empresa=instance,
            # Mapeamos el enunciado de la plantilla al campo actividad_tratamiento
            # que es el campo "título" de la pregunta en el modelo actual
            actividad_tratamiento=plantilla.enunciado,
            # Valores por defecto razonables — el coordinador los edita después
            categorias_datos='',
            descripcion_titulares='',
            finalidad_tratamiento='',
            base_legitimidad='consentimiento',
            periodo_conservacion=0,
            fuente_datos='',
            tipo=plantilla.tipo,
            responsable=responsable,
            version=None,
        ))

    RATPreguntas.objects.bulk_create(preguntas_a_crear)