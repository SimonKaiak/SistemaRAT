"""
vistas_generales.py
-------------------
Vistas principales del sistema: panel de inicio y visualización de
resultados de evaluación.

index(request)
    Vista de inicio con comportamiento distinto según el tipo de usuario:

    Superusuario:
    - Muestra el panel de administración con selector de empresa.
    - La empresa se obtiene por query param empresa_id o desde sesión.
    - No tiene equipo ni evaluaciones propias.
    - Template: index.html con es_admin_sistema=True.

    Trabajador:
    - Verifica si completó su autoevaluación.
    - Obtiene su equipo de subordinados directos.
    - Por cada subordinado calcula:
        - autoevaluacion_terminada: si finalizó su autoevaluación.
        - ya_evaluado: si el trabajador actual ya lo evaluó como jefe.
    - Template: index.html con es_admin_sistema=False.

ver_resultados(request, trabajador_id, tipo_evaluacion)
    Muestra los resultados de una evaluación (autoevaluación o
    evaluación de jefatura) agrupados por dimensión.

    Parámetros:
    - trabajador_id: trabajador cuyas respuestas se visualizan.
    - tipo_evaluacion: 'auto' para autoevaluación, cualquier otro
      valor para evaluación de jefatura (requiere evaluador_id en
      query param).
    - dimension_id (query param opcional): filtra por dimensión.

    Lógica:
    - Obtiene las respuestas según el tipo de evaluación.
    - Mapea cada respuesta a su TextosEvaluacion para obtener
      dimensión y competencia.
    - Agrupa las respuestas por dimensión en dimensiones_data.
    - Recoge el primer comentario de cada dimensión en
      comentarios_por_dimension.

    Contexto enviado al template (ver_resultados.html):
    trabajador, dimensiones, comentarios_por_dimension,
    fecha_cierre, visor_id, tipo_evaluacion.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from cuestionario.models import Trabajador, Autoevaluacion, EvaluacionJefatura, TextosEvaluacion, Empresa, InstrumentoEmpresa, RATRespuestas

@login_required
def index(request):
    # 1. VALIDACIÓN PARA ADMINISTRADOR
    if request.user.is_superuser:
        if request.GET.get('salir_empresa'):
            request.session.pop('empresa_id_admin', None)
            from django.shortcuts import redirect
            return redirect('/')
        empresa_id = request.GET.get('empresa_id') or request.session.get('empresa_id_admin')
        empresa_seleccionada = None
        if empresa_id:
            empresa_seleccionada = Empresa.objects.filter(id_empresa=empresa_id).first()
            request.session['empresa_id_admin'] = empresa_id
        instrumentos_rat = []
        if empresa_seleccionada:
            instrumentos_rat = InstrumentoEmpresa.objects.filter(
                empresa=empresa_seleccionada,
                habilitado=True,
                instrumento__tipo='rat'
            ).select_related('instrumento').order_by('instrumento__id_instrumento')

        context = {
            'es_admin_sistema': True,
            'nombre_usuario': request.user.username,
            'trabajador': None,
            'es_jefe': False,
            'equipo': [],
            'ya_hizo_autoevaluacion': False,
            'empresas_activas': Empresa.objects.filter(empresa_activa=True),
            'empresa_seleccionada': empresa_seleccionada,
            'instrumentos_rat': instrumentos_rat,
        }
        return render(request, 'cuestionario/index.html', context)

    # 2. FLUJO NORMAL PARA TRABAJADORES
    trabajador = get_object_or_404(Trabajador, user=request.user)
    
    autoeval_completada = Autoevaluacion.objects.filter(
        trabajador=trabajador, 
        estado_finalizacion=True
    ).exists()
    
    equipo = trabajador.subordinados.all()

    instrumentos_rat = InstrumentoEmpresa.objects.filter(
        empresa=trabajador.empresa,
        habilitado=True,
        instrumento__tipo='rat',
    ).select_related('instrumento').order_by('instrumento__id_instrumento')

    instrumentos_rat_list = list(instrumentos_rat)
    ie_rat1 = instrumentos_rat_list[0] if len(instrumentos_rat_list) > 0 else None
    ie_rat2 = instrumentos_rat_list[1] if len(instrumentos_rat_list) > 1 else None

    for sub in equipo:
        sub.autoevaluacion_terminada = Autoevaluacion.objects.filter(
            trabajador=sub, 
            estado_finalizacion=True
        ).exists()
        
        sub.ya_evaluado = EvaluacionJefatura.objects.filter(
            evaluador=trabajador, 
            trabajador_evaluado=sub,
            estado_finalizacion=True
        ).exists()

        if ie_rat1:
            total1 = ie_rat1.preguntas.exclude(
                actividad_tratamiento__istartswith='Presentación'
            ).count()
            respondidas1 = RATRespuestas.objects.filter(
                trabajador=sub, pregunta__instrumento_empresa=ie_rat1
            ).exclude(
                pregunta__actividad_tratamiento__istartswith='Presentación'
            ).values('pregunta').distinct().count()
            sub.rat1_listo = total1 > 0 and respondidas1 >= total1
            sub.rat1_progreso = f"{respondidas1}/{total1}"
        else:
            sub.rat1_listo = False

        if ie_rat2:
            total2 = ie_rat2.preguntas.exclude(
                actividad_tratamiento__istartswith='Presentación'
            ).count()
            respondidas2 = RATRespuestas.objects.filter(
                trabajador=sub, pregunta__instrumento_empresa=ie_rat2
            ).exclude(
                pregunta__actividad_tratamiento__istartswith='Presentación'
            ).values('pregunta').distinct().count()
            sub.rat2_listo = total2 > 0 and respondidas2 >= total2
            sub.rat2_progreso = f"{respondidas2}/{total2}"
        else:
            sub.rat2_listo = False

    rat1_instrumento_id = ie_rat1.instrumento.id_instrumento if ie_rat1 else None
    rat1_nombre = ie_rat1.instrumento.nombre_instrumento if ie_rat1 else 'RAT 1'
    rat2_instrumento_id = ie_rat2.instrumento.id_instrumento if ie_rat2 else None
    rat2_nombre = ie_rat2.instrumento.nombre_instrumento if ie_rat2 else 'RAT 2'

    context = {
        'trabajador': trabajador,
        'es_jefe': trabajador.subordinados.exists(),
        'equipo': equipo,
        'ya_hizo_autoevaluacion': autoeval_completada,
        'es_admin_sistema': False,
        'es_coordinador': trabajador.es_coordinador,
        'rat1_instrumento_id': rat1_instrumento_id,
        'rat1_nombre': rat1_nombre,
        'rat2_instrumento_id': rat2_instrumento_id,
        'rat2_nombre': rat2_nombre,
        'empresa_actual': trabajador.empresa,
    }
    return render(request, 'cuestionario/index.html', context)


@login_required
def ver_resultados(request, trabajador_id, tipo_evaluacion):
    trabajador_autenticado = get_object_or_404(Trabajador, user=request.user)
    trabajador_a_ver = get_object_or_404(Trabajador, id_trabajador=trabajador_id)
    empresa = trabajador_a_ver.empresa

    dimension_filtro = request.GET.get('dimension_id')

    if tipo_evaluacion == 'auto':
        respuestas = Autoevaluacion.objects.filter(
            trabajador=trabajador_a_ver,
        )
        visor_id = trabajador_a_ver.id_trabajador
    else:
        evaluador_id = request.GET.get('evaluador_id')
        respuestas = EvaluacionJefatura.objects.filter(
            trabajador_evaluado=trabajador_a_ver,
            evaluador_id=evaluador_id,
            estado_finalizacion=True
        )
        visor_id = evaluador_id

    codigos = list(respuestas.values_list('textos_evaluacion_codigo_excel', flat=True).distinct())

    textos_qs = TextosEvaluacion.objects.filter(
        empresa=empresa,
        codigo_excel__in=codigos
    ).select_related('dimension', 'competencia')

    if dimension_filtro:
        textos_qs = textos_qs.filter(dimension__id_dimension=dimension_filtro)

    textos_map = {t.codigo_excel: t for t in textos_qs}

    dimensiones_data = {}
    comentarios_por_dimension = {}
    for respuesta in respuestas:
        codigo = respuesta.textos_evaluacion_codigo_excel
        texto_eval = textos_map.get(codigo)
        if not texto_eval:
            continue

        dim_nombre = texto_eval.dimension.nombre_dimension
        if dim_nombre not in dimensiones_data:
            dimensiones_data[dim_nombre] = []
            comentarios_por_dimension[dim_nombre] = respuesta.comentario or ""

        respuesta.texto_eval = texto_eval
        dimensiones_data[dim_nombre].append(respuesta)

    context = {
        'trabajador': trabajador_a_ver,
        'dimensiones': dimensiones_data,
        'comentarios_por_dimension': comentarios_por_dimension,  # ← reemplaza 'comentario_final'
        'fecha_cierre': respuestas.first().momento_evaluacion if respuestas.exists() else None,
        'visor_id': visor_id,
        'tipo_evaluacion': tipo_evaluacion,
    }
    return render(request, 'cuestionario/ver_resultados.html', context)