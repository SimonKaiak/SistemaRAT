from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from cuestionario.models import (
    Empresa, Departamento, NivelJerarquico, Escala,
    Dimension, Competencia, Cargo, TextosEvaluacion,
    CodigoEvaluacion, Trabajador
)
import json


@login_required
def panel_poblador(request):
    if not request.user.is_superuser:
        return redirect('index')

    empresa_id = request.GET.get('empresa_id')
    empresa_actual = None

    if empresa_id:
        try:
            empresa_actual = Empresa.objects.get(id_empresa=empresa_id)
        except Empresa.DoesNotExist:
            pass

    context = {
        'empresa_actual': empresa_actual,
        'empresas': Empresa.objects.all().order_by('id_empresa'),
        'empresa_ya_registrada': Empresa.objects.exists(),
    }

    if empresa_actual:
        context['niveles'] = NivelJerarquico.objects.filter(empresa=empresa_actual).order_by('id_nivel_jerarquico')
        context['departamentos'] = Departamento.objects.filter(empresa=empresa_actual).order_by('id_departamento')
        context['escalas'] = Escala.objects.filter(empresa=empresa_actual).order_by('valor')
        context['dimensiones'] = Dimension.objects.filter(empresa=empresa_actual).order_by('id_dimension')
        context['competencias'] = Competencia.objects.filter(empresa=empresa_actual).select_related('dimension').order_by('dimension__id_dimension', 'id_competencia')
        context['cargos'] = Cargo.objects.filter(empresa=empresa_actual).select_related('nivel_jerarquico').order_by('nivel_jerarquico__id_nivel_jerarquico', 'id_cargo')
        context['textos'] = TextosEvaluacion.objects.filter(empresa=empresa_actual).select_related('dimension', 'competencia', 'nivel_jerarquico').order_by('dimension__id_dimension', 'competencia__id_competencia', 'nivel_jerarquico__id_nivel_jerarquico', 'id_textos_evaluacion')
        context['trabajadores'] = Trabajador.objects.filter(empresa=empresa_actual).select_related('cargo', 'nivel_jerarquico', 'departamento', 'id_jefe_directo').order_by('-nivel_jerarquico__id_nivel_jerarquico', 'id_trabajador')

    return render(request, 'cuestionario/poblador.html', context)


# ─────────────────────────────────────────────
# 1. EMPRESA
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_empresa(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    nombre = data.get('nombre_empresa', '').strip()
    rut = data.get('rut_empresa', '').strip()

    if not nombre or not rut:
        return JsonResponse({'ok': False, 'error': 'Nombre y RUT son obligatorios'})

    if Empresa.objects.filter(rut_empresa=rut).exists():
        return JsonResponse({'ok': False, 'error': f'Ya existe una empresa con RUT {rut}'})

    empresa = Empresa.objects.create(
        nombre_empresa=nombre,
        rut_empresa=rut,
        empresa_activa=True
    )
    return JsonResponse({'ok': True, 'id_empresa': empresa.id_empresa, 'nombre': empresa.nombre_empresa})


# ─────────────────────────────────────────────
# 2. DEPARTAMENTO
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_departamento(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    empresa_id = data.get('empresa_id')
    nombre = data.get('nombre_departamento', '').strip()

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio'})

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
    except Empresa.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Empresa no encontrada'})

    dep = Departamento.objects.create(nombre_departamento=nombre, empresa=empresa)
    return JsonResponse({'ok': True, 'id': dep.id_departamento, 'nombre': dep.nombre_departamento})


# ─────────────────────────────────────────────
# 3. NIVEL JERARQUICO
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_nivel(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    empresa_id = data.get('empresa_id')
    nombre = data.get('nombre_nivel', '').strip()

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio'})

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
    except Empresa.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Empresa no encontrada'})

    nivel = NivelJerarquico.objects.create(nombre_nivel_jerarquico=nombre, empresa=empresa)
    return JsonResponse({'ok': True, 'id': nivel.id_nivel_jerarquico, 'nombre': nivel.nombre_nivel_jerarquico})


# ─────────────────────────────────────────────
# 4. ESCALA
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_escala(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    empresa_id = data.get('empresa_id')
    filas = data.get('filas', [])

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
    except Empresa.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Empresa no encontrada'})

    if Escala.objects.filter(empresa=empresa).exists():
        return JsonResponse({'ok': False, 'error': 'La escala de esta empresa ya fue guardada'})

    if len(filas) != 4:
        return JsonResponse({'ok': False, 'error': 'La escala debe tener exactamente 4 valores'})

    creados = []
    for fila in filas:
        valor = fila.get('valor')
        titulo = fila.get('titulo', '').strip()
        descripcion = fila.get('descripcion', '').strip()
        if not titulo or not descripcion:
            return JsonResponse({'ok': False, 'error': f'Fila {valor}: título y descripción son obligatorios'})
        e = Escala.objects.create(valor=valor, titulo=titulo, descripcion=descripcion, empresa=empresa)
        creados.append({'id': e.id_escala, 'valor': e.valor, 'titulo': e.titulo})

    return JsonResponse({'ok': True, 'escalas': creados})


# ─────────────────────────────────────────────
# 5. DIMENSION
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_dimension(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    empresa_id = data.get('empresa_id')
    nombre = data.get('nombre_dimension', '').strip()

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio'})

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
    except Empresa.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Empresa no encontrada'})

    dim = Dimension.objects.create(nombre_dimension=nombre, empresa=empresa)
    return JsonResponse({'ok': True, 'id': dim.id_dimension, 'nombre': dim.nombre_dimension})


# ─────────────────────────────────────────────
# 6. COMPETENCIA
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_competencia(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    empresa_id = data.get('empresa_id')
    dimension_id = data.get('dimension_id')
    nombre = data.get('nombre_competencia', '').strip()

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio'})

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
        dimension = Dimension.objects.get(id_dimension=dimension_id, empresa=empresa)
    except (Empresa.DoesNotExist, Dimension.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'Empresa o dimensión no encontrada'})

    comp = Competencia.objects.create(nombre_competencia=nombre, dimension=dimension, empresa=empresa)
    return JsonResponse({'ok': True, 'id': comp.id_competencia, 'nombre': comp.nombre_competencia, 'dimension': dimension.nombre_dimension})


# ─────────────────────────────────────────────
# 7. CARGO
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_cargo(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    empresa_id = data.get('empresa_id')
    nivel_id = data.get('nivel_id')
    nombre = data.get('nombre_cargo', '').strip()

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio'})

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
        nivel = NivelJerarquico.objects.get(id_nivel_jerarquico=nivel_id, empresa=empresa)
    except (Empresa.DoesNotExist, NivelJerarquico.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'Empresa o nivel no encontrado'})

    cargo = Cargo.objects.create(nombre_cargo=nombre, nivel_jerarquico=nivel, empresa=empresa)
    return JsonResponse({'ok': True, 'id': cargo.id_cargo, 'nombre': cargo.nombre_cargo, 'nivel': nivel.nombre_nivel_jerarquico})


# ─────────────────────────────────────────────
# 8. TEXTO DE EVALUACION
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_texto(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    empresa_id = data.get('empresa_id')
    dimension_id = data.get('dimension_id')
    competencia_id = data.get('competencia_id')
    nivel_id = data.get('nivel_id')
    codigo = data.get('codigo_excel', '').strip()
    texto = data.get('texto', '').strip()

    if not codigo or not texto:
        return JsonResponse({'ok': False, 'error': 'Código y texto son obligatorios'})

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
        dimension = Dimension.objects.get(id_dimension=dimension_id, empresa=empresa)
        competencia = Competencia.objects.get(id_competencia=competencia_id, empresa=empresa)
        nivel = NivelJerarquico.objects.get(id_nivel_jerarquico=nivel_id, empresa=empresa)
    except (Empresa.DoesNotExist, Dimension.DoesNotExist, Competencia.DoesNotExist, NivelJerarquico.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'Referencia no encontrada'})

    if TextosEvaluacion.objects.filter(codigo_excel=codigo, empresa=empresa).exists():
        return JsonResponse({'ok': False, 'error': f'El código {codigo} ya existe para esta empresa'})

    texto_obj = TextosEvaluacion.objects.create(
        codigo_excel=codigo,
        texto=texto,
        empresa=empresa,
        dimension=dimension,
        competencia=competencia,
        nivel_jerarquico=nivel
    )

    CodigoEvaluacion.objects.create(
        empresa=empresa,
        dimension=dimension,
        competencia=competencia,
        nivel_jerarquico=nivel,
        textos_evaluacion_codigo_excel=codigo,
        textos_evaluacion_empresa=empresa
    )

    return JsonResponse({
        'ok': True,
        'id': texto_obj.id_textos_evaluacion,
        'codigo': texto_obj.codigo_excel,
        'texto': texto_obj.texto,
        'competencia': competencia.nombre_competencia,
        'nivel': nivel.nombre_nivel_jerarquico
    })


# ─────────────────────────────────────────────
# 9. TRABAJADOR
# ─────────────────────────────────────────────

@login_required
@require_POST
def guardar_trabajador(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    data = json.loads(request.body)
    empresa_id = data.get('empresa_id')
    rut = data.get('rut', '').strip()
    nombre = data.get('nombre', '').strip()
    ap_paterno = data.get('apellido_paterno', '').strip()
    ap_materno = data.get('apellido_materno', '').strip()
    email = data.get('email', '').strip()
    genero = data.get('genero', '').strip()
    es_coordinador = data.get('es_coordinador', False)
    nivel_id = data.get('nivel_id')
    cargo_id = data.get('cargo_id')
    departamento_id = data.get('departamento_id')
    jefe_id = data.get('jefe_id') or None

    if not all([rut, nombre, ap_paterno, ap_materno, email, genero, nivel_id, cargo_id, departamento_id]):
        return JsonResponse({'ok': False, 'error': 'Todos los campos son obligatorios excepto jefe directo'})

    if Trabajador.objects.filter(rut=rut).exists():
        return JsonResponse({'ok': False, 'error': f'Ya existe un trabajador con RUT {rut}'})

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
        nivel = NivelJerarquico.objects.get(id_nivel_jerarquico=nivel_id, empresa=empresa)
        cargo = Cargo.objects.get(id_cargo=cargo_id, empresa=empresa)
        departamento = Departamento.objects.get(id_departamento=departamento_id, empresa=empresa)
        jefe = Trabajador.objects.get(id_trabajador=jefe_id, empresa=empresa) if jefe_id else None
    except (Empresa.DoesNotExist, NivelJerarquico.DoesNotExist, Cargo.DoesNotExist, Departamento.DoesNotExist, Trabajador.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'Referencia no encontrada'})

    trabajador = Trabajador.objects.create(
        rut=rut,
        nombre=nombre,
        apellido_paterno=ap_paterno,
        apellido_materno=ap_materno,
        email=email,
        genero=genero,
        es_coordinador=es_coordinador,
        empresa=empresa,
        nivel_jerarquico=nivel,
        cargo=cargo,
        departamento=departamento,
        id_jefe_directo=jefe
    )

    return JsonResponse({
        'ok': True,
        'id': trabajador.id_trabajador,
        'nombre': f"{trabajador.nombre} {trabajador.apellido_paterno} {trabajador.apellido_materno}",
        'nivel': nivel.nombre_nivel_jerarquico,
        'cargo': cargo.nombre_cargo
    })


# ─────────────────────────────────────────────
# EDITAR EMPRESA
# ─────────────────────────────────────────────

@login_required
def editar_empresa(request, empresa_id):
    if not request.user.is_superuser:
        return redirect('index')
    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
    except Empresa.DoesNotExist:
        return redirect('panel_poblador')

    if request.method == 'POST':
        nombre = request.POST.get('nombre_empresa', '').strip()
        rut = request.POST.get('rut_empresa', '').strip()
        if nombre and rut:
            empresa.nombre_empresa = nombre
            empresa.rut_empresa = rut
            empresa.save()
            return redirect(f"/?empresa_id={empresa.id_empresa}")

    return render(request, 'cuestionario/editar_empresa.html', {'empresa': empresa})


# ─────────────────────────────────────────────
# ELIMINAR EMPRESA
# ─────────────────────────────────────────────

@login_required
@require_POST
def eliminar_empresa(request, empresa_id):
    if not request.user.is_superuser:
        return redirect('index')
    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
        empresa.delete()
    except Empresa.DoesNotExist:
        pass
    return redirect('panel_poblador')


# ─────────────────────────────────────────────
# CRUD INLINE — helpers
# ─────────────────────────────────────────────

def _empresa_id_de(obj):
    return obj.empresa.id_empresa


# ─── DEPARTAMENTO ────────────────────────────

@login_required
@require_POST
def editar_departamento(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    data = json.loads(request.body)
    try:
        dep = Departamento.objects.get(pk=pk)
        dep.nombre_departamento = data.get('nombre', dep.nombre_departamento).strip()
        dep.save()
        return JsonResponse({'ok': True, 'nombre': dep.nombre_departamento})
    except Departamento.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


@login_required
@require_POST
def eliminar_departamento(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        dep = Departamento.objects.get(pk=pk)
        dep.delete()
        return JsonResponse({'ok': True})
    except Departamento.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


# ─── NIVEL ───────────────────────────────────

@login_required
@require_POST
def editar_nivel(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    data = json.loads(request.body)
    try:
        nivel = NivelJerarquico.objects.get(pk=pk)
        nivel.nombre_nivel_jerarquico = data.get('nombre', nivel.nombre_nivel_jerarquico).strip()
        nivel.save()
        return JsonResponse({'ok': True, 'nombre': nivel.nombre_nivel_jerarquico})
    except NivelJerarquico.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


@login_required
@require_POST
def eliminar_nivel(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        NivelJerarquico.objects.get(pk=pk).delete()
        return JsonResponse({'ok': True})
    except NivelJerarquico.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


# ─── ESCALA ──────────────────────────────────

@login_required
@require_POST
def editar_escala_poblador(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    data = json.loads(request.body)
    try:
        escala = Escala.objects.get(pk=pk)
        escala.titulo = data.get('titulo', escala.titulo).strip()
        escala.descripcion = data.get('descripcion', escala.descripcion).strip()
        escala.save()
        return JsonResponse({'ok': True, 'titulo': escala.titulo, 'descripcion': escala.descripcion})
    except Escala.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


# ─── DIMENSION ───────────────────────────────

@login_required
@require_POST
def editar_dimension_poblador(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    data = json.loads(request.body)
    try:
        dim = Dimension.objects.get(pk=pk)
        dim.nombre_dimension = data.get('nombre', dim.nombre_dimension).strip()
        dim.save()
        return JsonResponse({'ok': True, 'nombre': dim.nombre_dimension})
    except Dimension.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


@login_required
@require_POST
def eliminar_dimension(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        Dimension.objects.get(pk=pk).delete()
        return JsonResponse({'ok': True})
    except Dimension.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


# ─── COMPETENCIA ─────────────────────────────

@login_required
@require_POST
def editar_competencia_poblador(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    data = json.loads(request.body)
    try:
        comp = Competencia.objects.get(pk=pk)
        comp.nombre_competencia = data.get('nombre', comp.nombre_competencia).strip()
        if data.get('dimension_id'):
            comp.dimension = Dimension.objects.get(pk=data['dimension_id'])
        comp.save()
        return JsonResponse({'ok': True, 'nombre': comp.nombre_competencia, 'dimension': comp.dimension.nombre_dimension})
    except (Competencia.DoesNotExist, Dimension.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


@login_required
@require_POST
def eliminar_competencia(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        Competencia.objects.get(pk=pk).delete()
        return JsonResponse({'ok': True})
    except Competencia.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


# ─── CARGO ───────────────────────────────────

@login_required
@require_POST
def editar_cargo_poblador(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    data = json.loads(request.body)
    try:
        cargo = Cargo.objects.get(pk=pk)
        cargo.nombre_cargo = data.get('nombre', cargo.nombre_cargo).strip()
        if data.get('nivel_id'):
            cargo.nivel_jerarquico = NivelJerarquico.objects.get(pk=data['nivel_id'])
        cargo.save()
        return JsonResponse({'ok': True, 'nombre': cargo.nombre_cargo, 'nivel': cargo.nivel_jerarquico.nombre_nivel_jerarquico})
    except (Cargo.DoesNotExist, NivelJerarquico.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


@login_required
@require_POST
def eliminar_cargo(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        Cargo.objects.get(pk=pk).delete()
        return JsonResponse({'ok': True})
    except Cargo.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


# ─── TEXTO EVALUACION ────────────────────────

@login_required
@require_POST
def editar_texto_poblador(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    data = json.loads(request.body)
    try:
        texto = TextosEvaluacion.objects.get(pk=pk)
        texto.codigo_excel = data.get('codigo', texto.codigo_excel).strip()
        texto.texto = data.get('texto', texto.texto).strip()
        texto.save()
        return JsonResponse({'ok': True, 'codigo': texto.codigo_excel, 'texto': texto.texto})
    except TextosEvaluacion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


@login_required
@require_POST
def eliminar_texto(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        TextosEvaluacion.objects.get(pk=pk).delete()
        return JsonResponse({'ok': True})
    except TextosEvaluacion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


# ─── TRABAJADOR ──────────────────────────────

@login_required
@require_POST
def editar_trabajador_poblador(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    data = json.loads(request.body)
    try:
        t = Trabajador.objects.get(pk=pk)
        t.nombre = data.get('nombre', t.nombre).strip()
        t.apellido_paterno = data.get('apellido_paterno', t.apellido_paterno).strip()
        t.apellido_materno = data.get('apellido_materno', t.apellido_materno).strip()
        t.email = data.get('email', t.email).strip()
        t.genero = data.get('genero', t.genero)
        t.es_coordinador = data.get('es_coordinador', t.es_coordinador)
        if data.get('nivel_id'):
            t.nivel_jerarquico = NivelJerarquico.objects.get(pk=data['nivel_id'])
        if data.get('cargo_id'):
            t.cargo = Cargo.objects.get(pk=data['cargo_id'])
        if data.get('departamento_id'):
            t.departamento = Departamento.objects.get(pk=data['departamento_id'])
        t.save()
        return JsonResponse({'ok': True, 'nombre': f"{t.nombre} {t.apellido_paterno}"})
    except Trabajador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})


@login_required
@require_POST
def eliminar_trabajador(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        Trabajador.objects.get(pk=pk).delete()
        return JsonResponse({'ok': True})
    except Trabajador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrado'})