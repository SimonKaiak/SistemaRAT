"""
vistas_seguimiento.py
---------------------
Vista para el detalle de seguimiento individual de un trabajador,
accesible por superusuarios y coordinadores de la misma empresa.

Endpoint: detalle_seguimiento(request, trabajador_id)

Control de acceso:
- Superusuario: acceso total.
- Coordinador: solo puede ver trabajadores de su propia empresa.
- Trabajador regular: redirige a index.

Lógica principal:
1. Obtiene el trabajador solicitado con sus relaciones (cargo,
   nivel jerárquico, jefe directo).
2. Recupera sus ResultadoConsolidado ordenados por código Excel.
3. Mapea cada resultado a su TextosEvaluacion correspondiente
   para obtener dimensión y competencia.
4. Agrupa los resultados por dimensión en dimensiones_data
   (usado por el template para renderizar secciones).
5. Calcula el promedio total de diferencia entre autoevaluación
   y evaluación de jefatura.
6. Recopila comentarios por dimensión separados en dos diccionarios:
   - comentarios_auto: primer comentario de autoevaluación por dimensión.
   - comentarios_jefe: primer comentario de jefatura por dimensión.

Contexto enviado al template (detalle_seguimiento.html):
- trabajador, dimensiones_data, diff_promedio_total,
  timestamp_auto, timestamp_jefe, comentarios_auto, comentarios_jefe.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from cuestionario.models import Trabajador, Autoevaluacion, EvaluacionJefatura, ResultadoConsolidado, TextosEvaluacion, Dimension

@login_required
def detalle_seguimiento(request, trabajador_id):
    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
        except Trabajador.DoesNotExist:
            return redirect('index')
    else:
        trabajador_actual = None

    try:
        trabajador = Trabajador.objects.select_related(
            'cargo', 'nivel_jerarquico', 'id_jefe_directo'
        ).get(id_trabajador=trabajador_id)
    except Trabajador.DoesNotExist:
        return redirect('seguimiento_admin')

    # Coordinador solo puede ver trabajadores de su empresa
    if trabajador_actual and trabajador.empresa != trabajador_actual.empresa:
        return redirect('index')

    empresa = trabajador.empresa

    resultados = ResultadoConsolidado.objects.filter(
        trabajador=trabajador
    ).order_by('textos_evaluacion_codigo_excel')

    codigos = list(resultados.values_list('textos_evaluacion_codigo_excel', flat=True).distinct())

    textos_qs = TextosEvaluacion.objects.filter(
        empresa=empresa,
        codigo_excel__in=codigos
    ).select_related('dimension', 'competencia')

    textos_map = {t.codigo_excel: t for t in textos_qs}

    dimensiones_data = {}
    for r in resultados:
        texto_eval = textos_map.get(r.textos_evaluacion_codigo_excel)
        if not texto_eval:
            continue
        r.texto_eval = texto_eval
        dim_nombre = texto_eval.dimension.nombre_dimension
        if dim_nombre not in dimensiones_data:
            dimensiones_data[dim_nombre] = []
        dimensiones_data[dim_nombre].append(r)

    diff_promedio_total = resultados.aggregate(Avg('diferencia'))['diferencia__avg']

    auto = Autoevaluacion.objects.filter(trabajador=trabajador, estado_finalizacion=True).first()
    jefe = EvaluacionJefatura.objects.filter(trabajador_evaluado=trabajador, estado_finalizacion=True).first()

    # Comentarios por dimension - Autoevaluacion
    comentarios_auto = {}
    autoevals = Autoevaluacion.objects.filter(trabajador=trabajador, estado_finalizacion=True)
    for ae in autoevals:
        texto_eval = textos_map.get(ae.textos_evaluacion_codigo_excel)
        if not texto_eval:
            continue
        dim_nombre = texto_eval.dimension.nombre_dimension
        if dim_nombre not in comentarios_auto and ae.comentario:
            comentarios_auto[dim_nombre] = ae.comentario

    # Comentarios por dimension - Evaluacion Jefatura
    comentarios_jefe = {}
    jefaturas = EvaluacionJefatura.objects.filter(trabajador_evaluado=trabajador, estado_finalizacion=True)
    for ej in jefaturas:
        texto_eval = textos_map.get(ej.textos_evaluacion_codigo_excel)
        if not texto_eval:
            continue
        dim_nombre = texto_eval.dimension.nombre_dimension
        if dim_nombre not in comentarios_jefe and ej.comentario:
            comentarios_jefe[dim_nombre] = ej.comentario

    context = {
        'trabajador': trabajador,
        'dimensiones_data': dimensiones_data,
        'diff_promedio_total': diff_promedio_total,
        'timestamp_auto': auto.momento_evaluacion if auto else None,
        'timestamp_jefe': jefe.momento_evaluacion if jefe else None,
        'comentarios_auto': comentarios_auto,
        'comentarios_jefe': comentarios_jefe,
    }

    return render(request, 'cuestionario/detalle_seguimiento.html', context)