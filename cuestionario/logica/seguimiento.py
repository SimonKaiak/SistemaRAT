"""
seguimiento.py
---------------------------
Vista para el panel de seguimiento general del estado de evaluaciones
de todos los trabajadores de una empresa.
Accesible por superusuarios y coordinadores.

panel_seguimiento(request)
    Muestra el estado de avance de autoevaluaciones y evaluaciones
    de jefatura para cada trabajador de la empresa seleccionada.

    Control de acceso:
    - Superusuario: filtra por empresa vía query param empresa_id.
    - Coordinador: ve solo los trabajadores de su propia empresa.
    - Trabajador regular: redirige a index.

    Por cada trabajador calcula:
    - auto_lista: si tiene autoevaluación finalizada.
    - tiene_jefe / jefe_lista: si tiene jefe asignado y si su
      evaluación de jefatura está finalizada.
    - diff_promedio: promedio de diferencia entre puntaje jefe y
      autoevaluación (solo si ambas evaluaciones están completas).

    Contadores globales enviados al template:
    - autos_listas / autos_pendientes
    - jefaturas_listas / jefaturas_pendientes
    - total_pendientes: suma de autoevaluaciones y jefaturas aún
      sin completar.

    Contexto enviado al template (seguimiento.html):
    trabajadores, total_pendientes, autos_listas, autos_pendientes,
    jefaturas_listas, jefaturas_pendientes, empresa_actual,
    es_coordinador.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from cuestionario.models import Trabajador, Autoevaluacion, EvaluacionJefatura, ResultadoConsolidado, Empresa, RATRespuestas, InstrumentoEmpresa

@login_required
def panel_seguimiento(request):
    es_coordinador = False
    empresa_actual = None

    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
            es_coordinador = True
            empresa_actual = trabajador_actual.empresa
        except Trabajador.DoesNotExist:
            return redirect('index')
    else:
        empresa_id = request.GET.get('empresa_id')
        if empresa_id:
            try:
                empresa_actual = Empresa.objects.get(id_empresa=empresa_id)
            except Empresa.DoesNotExist:
                pass

    if empresa_actual:
        trabajadores = Trabajador.objects.filter(
            empresa=empresa_actual
        ).select_related('cargo', 'empresa').order_by('-nivel_jerarquico__id_nivel_jerarquico')
    else:
        trabajadores = Trabajador.objects.none()

    autos_listas = 0
    autos_pendientes = 0
    jefaturas_listas = 0
    jefaturas_pendientes = 0
    total_por_realizar = 0
    rat_listos = 0
    rat_pendientes = 0

    instrumento_empresa_rat = None
    if empresa_actual:
        instrumento_empresa_rat = InstrumentoEmpresa.objects.filter(empresa=empresa_actual, habilitado=True, instrumento__tipo='rat').first()

    for t in trabajadores:
        t.auto_lista = Autoevaluacion.objects.filter(trabajador=t, estado_finalizacion=True).exists()
        if t.auto_lista:
            autos_listas += 1
        else:
            autos_pendientes += 1
            total_por_realizar += 1

        if t.id_jefe_directo:
            t.tiene_jefe = True
            t.jefe_lista = EvaluacionJefatura.objects.filter(trabajador_evaluado=t, estado_finalizacion=True).exists()
            if t.jefe_lista:
                jefaturas_listas += 1
            else:
                jefaturas_pendientes += 1
                total_por_realizar += 1
        else:
            t.tiene_jefe = False
            t.jefe_lista = False

        t.diff_promedio = None
        if t.auto_lista and (not t.tiene_jefe or t.jefe_lista):
            res = ResultadoConsolidado.objects.filter(trabajador=t).aggregate(Avg('diferencia'))
            t.diff_promedio = res['diferencia__avg']

        if instrumento_empresa_rat:
            total_preguntas = instrumento_empresa_rat.preguntas.count()
            respondidas = RATRespuestas.objects.filter(trabajador=t, pregunta__instrumento_empresa=instrumento_empresa_rat).values('pregunta').distinct().count()
            t.rat_listo = total_preguntas > 0 and respondidas >= total_preguntas
        else:
            t.rat_listo = False
        if t.rat_listo:
            rat_listos += 1
        else:
            rat_pendientes += 1

    context = {
        'trabajadores': trabajadores,
        'total_pendientes': total_por_realizar,
        'autos_listas': autos_listas,
        'autos_pendientes': autos_pendientes,
        'jefaturas_listas': jefaturas_listas,
        'jefaturas_pendientes': jefaturas_pendientes,
        'rat_listos': rat_listos,
        'rat_pendientes': rat_pendientes,
        'empresa_actual': empresa_actual,
        'es_coordinador': es_coordinador,
    }
    return render(request, 'cuestionario/seguimiento.html', context)


@login_required
def panel_seguimiento_rat(request):
    es_coordinador = False
    empresa_actual = None

    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
            es_coordinador = True
            empresa_actual = trabajador_actual.empresa
        except Trabajador.DoesNotExist:
            return redirect('index')
    else:
        empresa_id = request.GET.get('empresa_id') or request.session.get('empresa_id_admin')
        if empresa_id:
            try:
                empresa_actual = Empresa.objects.get(id_empresa=empresa_id)
            except Empresa.DoesNotExist:
                pass

    if empresa_actual:
        trabajadores = Trabajador.objects.filter(
            empresa=empresa_actual
        ).select_related('cargo', 'empresa').order_by('-nivel_jerarquico__id_nivel_jerarquico')
    else:
        trabajadores = Trabajador.objects.none()

    rat_listos = 0
    rat_pendientes = 0

    instrumento_empresa_rat = None
    if empresa_actual:
        instrumento_empresa_rat = InstrumentoEmpresa.objects.filter(
            empresa=empresa_actual, habilitado=True, instrumento__tipo='rat'
        ).first()

    for t in trabajadores:
        if instrumento_empresa_rat:
            total_preguntas = instrumento_empresa_rat.preguntas.count()
            respondidas = RATRespuestas.objects.filter(
                trabajador=t, pregunta__instrumento_empresa=instrumento_empresa_rat
            ).values('pregunta').distinct().count()
            t.rat_listo = total_preguntas > 0 and respondidas >= total_preguntas
        else:
            t.rat_listo = False
        if t.rat_listo:
            rat_listos += 1
        else:
            rat_pendientes += 1

    context = {
        'trabajadores': trabajadores,
        'rat_listos': rat_listos,
        'rat_pendientes': rat_pendientes,
        'empresa_actual': empresa_actual,
        'es_coordinador': es_coordinador,
    }
    return render(request, 'cuestionario/seguimiento_rat.html', context)