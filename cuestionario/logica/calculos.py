"""
calculos.py
--------------
Módulo utilitario encargado de generar o actualizar el resultado
consolidado de un trabajador para un período determinado.

Función principal: generar_consolidado(trabajador, periodo)
- Cruza las respuestas de autoevaluación con las de evaluación de
  jefatura (si existe jefe asignado) pregunta por pregunta.
- Para cada pregunta calcula el puntaje del jefe y la diferencia
  respecto a la autoevaluación.
- Si el trabajador no tiene jefe, el puntaje jefe y la diferencia
  se registran como 0.
- Navega por CodigoEvaluacion para obtener dimensión, competencia
  y nivel jerárquico asociados a cada respuesta.
- Guarda o actualiza el resultado en ResultadoConsolidado
  (update_or_create por trabajador + código + período).

Notas:
- Los cálculos de promedios por dimensión, competencia y general
  están comentados y pendientes de implementación futura.
- El campo evaluacion_jefatura en ResultadoConsolidado acepta null
  para cubrir el caso de trabajadores sin jefe directo.
"""
from django.db.models import Avg
from datetime import datetime
from cuestionario.models import (
    Autoevaluacion, EvaluacionJefatura, ResultadoConsolidado, 
    Trabajador, CodigoEvaluacion
)


def generar_consolidado(trabajador, periodo=None):
    if not periodo:
        periodo = datetime.now().year

    # 1. Obtener todas las respuestas de autoevaluación finalizadas
    respuestas_auto = Autoevaluacion.objects.filter(
        trabajador=trabajador, 
        estado_finalizacion=True
    )
    
    if not respuestas_auto.exists():
        return

    # 2. Verificar si el trabajador tiene un jefe asignado
    tiene_jefe = trabajador.id_jefe_directo is not None

    # 3. Obtener respuestas de la jefatura (si aplica)
    respuestas_jefe = EvaluacionJefatura.objects.filter(
        trabajador_evaluado=trabajador, 
        estado_finalizacion=True
    )

    empresa = trabajador.empresa

    # 4. Cálculo del Promedio General (COMENTADO DE MOMENTO)
    # if tiene_jefe and respuestas_jefe.exists():
    #     prom_gral = respuestas_jefe.aggregate(Avg('puntaje'))['puntaje__avg']
    # else:
    #     prom_gral = respuestas_auto.aggregate(Avg('puntaje'))['puntaje__avg']

    # 5. Iterar sobre cada pregunta de la autoevaluación para cruzar datos
    for r_auto in respuestas_auto:
        p_jefe = 0
        diff = 0
        r_jefe_obj = None

        # LÓGICA DE CRUCES:
        if tiene_jefe and respuestas_jefe.exists():
            # Si tiene jefe, buscamos la respuesta espejo por código
            r_jefe_obj = respuestas_jefe.filter(
                textos_evaluacion_codigo_excel=r_auto.textos_evaluacion_codigo_excel
            ).first()
            if r_jefe_obj:
                p_jefe = r_jefe_obj.puntaje
                diff = p_jefe - r_auto.puntaje
        else:
            # SI NO TIENE JEFE: forzamos puntaje jefe y diferencia a 0
            # r_jefe_obj queda None → OK porque evaluacion_jefatura es null=True ahora
            p_jefe = 0
            diff = 0

        # En v3 codigo_excel es CharField → usamos CODIGO_EVALUACION para navegar
        # (que tiene dimension, competencia y nivel_jerarquico denormalizados)
        codigo_eval = CodigoEvaluacion.objects.filter(
            empresa=empresa,
            textos_evaluacion_codigo_excel=r_auto.textos_evaluacion_codigo_excel
        ).first()

        if not codigo_eval:
            continue

        comp = codigo_eval.competencia
        dim = codigo_eval.dimension
        nivel = codigo_eval.nivel_jerarquico

        # Calcular promedios específicos (COMENTADO DE MOMENTO)
        # if tiene_jefe and respuestas_jefe.exists():
        #     codigos_dim = CodigoEvaluacion.objects.filter(empresa=empresa, dimension=dim).values_list('textos_evaluacion_codigo_excel', flat=True)
        #     codigos_comp = CodigoEvaluacion.objects.filter(empresa=empresa, competencia=comp).values_list('textos_evaluacion_codigo_excel', flat=True)
        #     prom_dim = respuestas_jefe.filter(textos_evaluacion_codigo_excel__in=codigos_dim).aggregate(Avg('puntaje'))['puntaje__avg']
        #     prom_comp = respuestas_jefe.filter(textos_evaluacion_codigo_excel__in=codigos_comp).aggregate(Avg('puntaje'))['puntaje__avg']
        # else:
        #     codigos_dim = CodigoEvaluacion.objects.filter(empresa=empresa, dimension=dim).values_list('textos_evaluacion_codigo_excel', flat=True)
        #     codigos_comp = CodigoEvaluacion.objects.filter(empresa=empresa, competencia=comp).values_list('textos_evaluacion_codigo_excel', flat=True)
        #     prom_dim = respuestas_auto.filter(textos_evaluacion_codigo_excel__in=codigos_dim).aggregate(Avg('puntaje'))['puntaje__avg']
        #     prom_comp = respuestas_auto.filter(textos_evaluacion_codigo_excel__in=codigos_comp).aggregate(Avg('puntaje'))['puntaje__avg']

        # 6. Guardar o actualizar en la tabla ResultadoConsolidado
        ResultadoConsolidado.objects.update_or_create(
            trabajador=trabajador,
            textos_evaluacion_codigo_excel=r_auto.textos_evaluacion_codigo_excel,
            periodo=periodo,
            defaults={
                'puntaje_autoev': r_auto.puntaje,
                'puntaje_jefe': p_jefe,
                'diferencia': diff,
                # 'prom_competencia': prom_comp,
                # 'prom_dimension': prom_dim,
                # 'prom_general': prom_gral,
                'textos_evaluacion_empresa': empresa,
                'autoevaluacion': r_auto,
                'evaluacion_jefatura': r_jefe_obj,  # None si no tiene jefe (null=True en BD)
            }
        )