from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from cuestionario.models import Trabajador, Autoevaluacion, EvaluacionJefatura, TextosEvaluacion, Empresa

@login_required
def index(request):
    # 1. VALIDACIÓN PARA ADMINISTRADOR
    if request.user.is_superuser:
        context = {
            'es_admin_sistema': True,
            'nombre_usuario': request.user.username,
            'trabajador': None,
            'es_jefe': False,
            'equipo': [],
            'ya_hizo_autoevaluacion': False,
            'empresas_activas': Empresa.objects.filter(empresa_activa=True),
        }
        return render(request, 'cuestionario/index.html', context)

    # 2. FLUJO NORMAL PARA TRABAJADORES
    trabajador = get_object_or_404(Trabajador, user=request.user)
    
    autoeval_completada = Autoevaluacion.objects.filter(
        trabajador=trabajador, 
        estado_finalizacion=True
    ).exists()
    
    equipo = trabajador.subordinados.all()
    
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

    context = {
        'trabajador': trabajador,
        'es_jefe': trabajador.subordinados.exists(),
        'equipo': equipo,
        'ya_hizo_autoevaluacion': autoeval_completada,
        'es_admin_sistema': False,
        'es_coordinador': trabajador.es_coordinador, 
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
            estado_finalizacion=True
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