from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages  
from cuestionario.models import Empresa, Dimension, Competencia, TextosEvaluacion, NivelJerarquico, Escala, Trabajador


@login_required
def panel_edicion(request):
    es_coordinador = False
    empresa_actual = None

    if request.user.is_superuser:
        empresa_id = request.GET.get('empresa_id') or request.session.get('empresa_id_admin')
        if empresa_id:
            request.session['empresa_id_admin'] = empresa_id
            try:
                empresa_actual = Empresa.objects.get(id_empresa=empresa_id)
            except Empresa.DoesNotExist:
                pass
    else:
        try:
            trabajador = Trabajador.objects.get(user=request.user)
            if not trabajador.es_coordinador:
                return redirect('index')
            es_coordinador = True
            empresa_actual = trabajador.empresa
        except Trabajador.DoesNotExist:
            return redirect('index')

    dimensiones = []
    competencias = []
    niveles = []
    textos = []
    escalas = []

    if empresa_actual:
        dimensiones = Dimension.objects.filter(empresa=empresa_actual)
        competencias = Competencia.objects.filter(empresa=empresa_actual).select_related('dimension')
        niveles = NivelJerarquico.objects.filter(empresa=empresa_actual)
        textos = TextosEvaluacion.objects.filter(empresa=empresa_actual).select_related(
            'dimension', 'competencia', 'nivel_jerarquico'
        ).order_by('id_textos_evaluacion')
        escalas = Escala.objects.filter(empresa=empresa_actual).order_by('valor')

    context = {
        'empresas': Empresa.objects.filter(empresa_activa=True),
        'empresa_actual': empresa_actual,
        'dimensiones': dimensiones,
        'competencias': competencias,
        'niveles': niveles,
        'textos': textos,
        'escalas': escalas,
        'es_coordinador': es_coordinador,
    }
    return render(request, 'cuestionario/edicion_cuestionario.html', context)


def _get_trabajador_o_redirigir(request):
    """Retorna el trabajador si es coordinador, o None si debe redirigirse."""
    if request.user.is_superuser:
        return None  # superuser no necesita validación de empresa
    try:
        trabajador = Trabajador.objects.get(user=request.user)
        if not trabajador.es_coordinador:
            return 'redirect'
        return trabajador
    except Trabajador.DoesNotExist:
        return 'redirect'


@login_required
def editar_dimension(request, dimension_id):
    trabajador = _get_trabajador_o_redirigir(request)
    if trabajador == 'redirect':
        return redirect('index')

    dimension = get_object_or_404(Dimension, id_dimension=dimension_id)

    # Verificar que la dimensión pertenece a la empresa del coordinador
    if trabajador and dimension.empresa != trabajador.empresa:
        return redirect('index')

    if request.method == 'POST':
        nombre = request.POST.get('nombre_dimension', '').strip()
        if nombre:
            dimension.nombre_dimension = nombre
            dimension.save()
            messages.success(request, f'✅ Dimensión "{nombre}" actualizada correctamente.')
        return redirect(f'/edicion/?empresa_id={dimension.empresa.id_empresa}')

    return redirect('panel_edicion')


@login_required
def editar_competencia(request, competencia_id):
    trabajador = _get_trabajador_o_redirigir(request)
    if trabajador == 'redirect':
        return redirect('index')

    competencia = get_object_or_404(Competencia, id_competencia=competencia_id)

    # Verificar que la competencia pertenece a la empresa del coordinador
    if trabajador and competencia.empresa != trabajador.empresa:
        return redirect('index')

    if request.method == 'POST':
        nombre = request.POST.get('nombre_competencia', '').strip()
        if nombre:
            competencia.nombre_competencia = nombre
            competencia.save()
            messages.success(request, f'✅ Competencia "{nombre}" actualizada correctamente.')
        return redirect(f'/edicion/?empresa_id={competencia.empresa.id_empresa}')

    return redirect('panel_edicion')


@login_required
def editar_nivel(request, nivel_id):
    trabajador = _get_trabajador_o_redirigir(request)
    if trabajador == 'redirect':
        return redirect('index')

    nivel = get_object_or_404(NivelJerarquico, id_nivel_jerarquico=nivel_id)

    # Verificar que el nivel pertenece a la empresa del coordinador
    if trabajador and nivel.empresa != trabajador.empresa:
        return redirect('index')

    if request.method == 'POST':
        nombre = request.POST.get('nombre_nivel_jerarquico', '').strip()
        if nombre:
            nivel.nombre_nivel_jerarquico = nombre
            nivel.save()
            messages.success(request, f'✅ Nivel jerárquico "{nombre}" actualizado correctamente.')
        return redirect(f'/edicion/niveles/?empresa_id={nivel.empresa.id_empresa}')

    return redirect('panel_edicion')


@login_required
def editar_texto(request, texto_id):
    trabajador = _get_trabajador_o_redirigir(request)
    if trabajador == 'redirect':
        return redirect('index')

    texto = get_object_or_404(TextosEvaluacion, id_textos_evaluacion=texto_id)

    # Verificar que el texto pertenece a la empresa del coordinador
    if trabajador and texto.empresa != trabajador.empresa:
        return redirect('index')

    if request.method == 'POST':
        nuevo_texto = request.POST.get('texto', '').strip()
        if nuevo_texto:
            texto.texto = nuevo_texto
            texto.save()
            messages.success(request, f'✅ Texto "{texto.codigo_excel}" actualizado correctamente.')
        return redirect(f'/edicion/?empresa_id={texto.empresa.id_empresa}')

    return redirect('panel_edicion')


@login_required
def editar_escala(request, escala_id):
    trabajador = _get_trabajador_o_redirigir(request)
    if trabajador == 'redirect':
        return redirect('index')

    escala = get_object_or_404(Escala, id_escala=escala_id)

    # Verificar que la escala pertenece a la empresa del coordinador
    if trabajador and escala.empresa != trabajador.empresa:
        return redirect('index')

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if titulo:
            escala.titulo = titulo
        if descripcion:
            escala.descripcion = descripcion
        escala.save()
        messages.success(request, f'✅ Escala "{escala.titulo}" actualizada correctamente.')
        return redirect(f'/edicion/?empresa_id={escala.empresa.id_empresa}')

    return redirect('panel_edicion')


@login_required
def panel_edicion_niveles(request):
    es_coordinador = False
    empresa_actual = None

    if request.user.is_superuser:
        empresa_id = request.GET.get('empresa_id') or request.session.get('empresa_id_admin')
        if empresa_id:
            request.session['empresa_id_admin'] = empresa_id
            try:
                empresa_actual = Empresa.objects.get(id_empresa=empresa_id)
            except Empresa.DoesNotExist:
                pass
    else:
        try:
            trabajador = Trabajador.objects.get(user=request.user)
            if not trabajador.es_coordinador:
                return redirect('index')
            es_coordinador = True
            empresa_actual = trabajador.empresa
        except Trabajador.DoesNotExist:
            return redirect('index')

    niveles = NivelJerarquico.objects.filter(empresa=empresa_actual) if empresa_actual else []

    context = {
        'empresa_actual': empresa_actual,
        'niveles': niveles,
        'es_coordinador': es_coordinador,
    }
    return render(request, 'cuestionario/edicion_niveles.html', context)