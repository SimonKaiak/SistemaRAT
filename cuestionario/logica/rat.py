"""
rat.py
------
Vistas y formularios para el módulo RAT (Registro de Actividades
de Tratamiento). Gestiona el flujo completo para trabajadores,
coordinadores y superusuarios.

Helpers internos:

_get_trabajador_o_none(request)
    Retorna el Trabajador del usuario autenticado o None si no existe.

_get_instrumento_empresa(request, empresa)
    Obtiene el InstrumentoEmpresa activo para la empresa, usando el
    query param instrumento_id. Si no se especifica, retorna el primer
    instrumento RAT habilitado de la empresa.

_get_empresa_y_trabajador(request)
    Retorna (empresa, trabajador) según sea superusuario (empresa por
    sesión/query param) o coordinador (empresa propia).

Formularios:

RATRespuestaForm     → Formulario para que el trabajador ingrese su
                       respuesta a una pregunta RAT (campo textarea).
RATPreguntaForm      → Formulario completo para crear/editar una
                       RATPreguntas. Filtra responsable y versión por
                       empresa. El campo versión es opcional.
RegistroVersionesForm → Formulario para crear/editar versiones del RAT.

Vistas del trabajador:

rat_panel_usuario(request)
    Muestra al trabajador sus preguntas RAT y respuestas existentes
    para el instrumento habilitado de su empresa.
    Template: rat_usuario.html

rat_responder(request, pregunta_id)
    Permite al trabajador crear o editar su respuesta a una pregunta
    RAT específica. Redirige al panel tras guardar.
    Template: rat_responder.html

Vistas del coordinador/superusuario:

rat_panel_coordinador(request)
    Muestra todas las preguntas RAT del instrumento activo con sus
    respuestas por trabajador.
    Template: rat_coordinador.html

rat_nueva_pregunta(request)
    Crea una nueva RATPreguntas asociada al InstrumentoEmpresa activo.
    Template: rat_formulario.html

rat_editar_pregunta(request, pregunta_id)
    Edita una RATPreguntas existente del instrumento activo.
    Template: rat_formulario.html

rat_eliminar_pregunta(request, pregunta_id)
    Elimina una RATPreguntas tras confirmación POST.
    Template: rat_confirmar_eliminar.html

Vistas de versiones (solo coordinador):

rat_versiones(request)
    Lista las versiones del RAT de la empresa del coordinador.
    Template: rat_versiones.html

rat_nueva_version(request)
    Crea un nuevo RegistroVersiones para la empresa.
    Template: rat_nueva_version.html

rat_editar_version(request, version_id)
    Edita un RegistroVersiones existente de la empresa.
    Template: rat_nueva_version.html

rat_eliminar_version(request, version_id)
    Elimina un RegistroVersiones tras confirmación POST.
    Template: rat_confirmar_eliminar_version.html

Vistas de instrumentos:

seleccion_instrumentos(request)
    Muestra los instrumentos habilitados de la empresa separados en
    dos listas: instrumentos RAT e instrumentos de otro tipo (ej:
    Eval Desempeño). Punto de entrada principal tras el login.
    Template: seleccion_instrumentos.html

rat_crear_instrumento(request)
    Crea un nuevo Instrumento global y lo asigna a la empresa via
    InstrumentoEmpresa (habilitado=True). Usa get_or_create para
    evitar duplicados. Al crear un instrumento nuevo se dispara
    automáticamente la señal clonar_preguntas_rat.
    Template: rat_crear_instrumento.html
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django import forms
from cuestionario.models import (
    RATPreguntas, RATRespuestas, RegistroVersiones,
    Trabajador, Empresa, Instrumento, InstrumentoEmpresa,
)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _get_trabajador_o_none(request):
    try:
        return Trabajador.objects.get(user=request.user)
    except Trabajador.DoesNotExist:
        return None


def _get_instrumento_empresa(request, empresa):
    """
    Devuelve el InstrumentoEmpresa pedido por query-param `instrumento_id`,
    validando que esté habilitado para esa empresa.
    instrumento_id se refiere al id del Instrumento (no del InstrumentoEmpresa).
    """
    instrumento_id = request.GET.get('instrumento_id')
    if instrumento_id:
        return get_object_or_404(
            InstrumentoEmpresa,
            instrumento__id_instrumento=instrumento_id,
            empresa=empresa,
            habilitado=True,
        )
    # fallback: primer instrumento de tipo RAT habilitado de la empresa
    return InstrumentoEmpresa.objects.filter(
        empresa=empresa,
        habilitado=True,
        instrumento__tipo='rat',
    ).select_related('instrumento').first()


# ─── FORMS ────────────────────────────────────────────────────────────────────

class RATRespuestaForm(forms.ModelForm):
    class Meta:
        model = RATRespuestas
        fields = ['respuesta']
        widgets = {
            'respuesta': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Escribe tu respuesta aquí...',
                'style': 'width:100%; padding:0.6em; border-radius:6px; border:1px solid rgba(255,255,255,0.2); background:rgba(255,255,255,0.05); color:#fff; font-size:0.95em;',
            }),
        }


class RATPreguntaForm(forms.ModelForm):
    class Meta:
        model = RATPreguntas
        fields = [
            'actividad_tratamiento',
            'responsable',
            'categorias_datos',
            'descripcion_titulares',
            'finalidad_tratamiento',
            'base_legitimidad',
            'periodo_conservacion',
            'fuente_datos',
            'version',
        ]
        widgets = {
            'actividad_tratamiento': forms.TextInput(attrs={
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);color:#fff;',
                'placeholder': 'Ej: Gestión de nóminas y remuneraciones',
            }),
            'responsable': forms.Select(attrs={
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(30,30,50,0.9);color:#fff;',
            }),
            'categorias_datos': forms.Textarea(attrs={
                'rows': 2,
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);color:#fff;',
                'placeholder': 'Ej: Datos identificativos (RUT, nombre)',
            }),
            'descripcion_titulares': forms.Textarea(attrs={
                'rows': 2,
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);color:#fff;',
                'placeholder': 'Ej: Trabajadores y ex-trabajadores de la empresa',
            }),
            'finalidad_tratamiento': forms.Textarea(attrs={
                'rows': 2,
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);color:#fff;',
                'placeholder': 'Ej: Calcular y pagar remuneraciones',
            }),
            'base_legitimidad': forms.Select(attrs={
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(30,30,50,0.9);color:#fff;',
            }),
            'periodo_conservacion': forms.NumberInput(attrs={
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);color:#fff;',
                'placeholder': 'Ej: 60 (meses)',
            }),
            'fuente_datos': forms.TextInput(attrs={
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);color:#fff;',
                'placeholder': 'Ej: El propio trabajador mediante contrato de trabajo',
            }),
            'version': forms.Select(attrs={
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(30,30,50,0.9);color:#fff;',
            }),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['responsable'].queryset = Trabajador.objects.filter(empresa=empresa)
            self.fields['version'].queryset = RegistroVersiones.objects.filter(empresa=empresa)
        else:
            self.fields['responsable'].queryset = Trabajador.objects.all()
            self.fields['version'].queryset = RegistroVersiones.objects.all()
        self.fields['version'].required = False


class RegistroVersionesForm(forms.ModelForm):
    class Meta:
        model = RegistroVersiones
        fields = ['version', 'motivo_modificacion']
        widgets = {
            'version': forms.TextInput(attrs={
                'placeholder': 'Ej: 1.0, 1.1, 2.0',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);color:#fff;',
            }),
            'motivo_modificacion': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe por qué se modifica esta versión...',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);color:#fff;',
            }),
        }


# ─── VISTAS TRABAJADOR ────────────────────────────────────────────────────────

@login_required
def rat_panel_usuario(request):
    trabajador = _get_trabajador_o_none(request)
    if not trabajador:
        return redirect('index')

    ie = _get_instrumento_empresa(request, trabajador.empresa)
    if not ie:
        return render(request, 'cuestionario/rat_usuario.html', {
            'trabajador': trabajador,
            'preguntas': [],
            'respuestas_existentes': {},
            'instrumento': None,
            'sin_instrumento': True,
        })

    preguntas = RATPreguntas.objects.filter(instrumento_empresa=ie)
    respuestas_existentes = {
        r.pregunta_id: r
        for r in RATRespuestas.objects.filter(trabajador=trabajador, pregunta__instrumento_empresa=ie)
    }

    return render(request, 'cuestionario/rat_usuario.html', {
        'trabajador': trabajador,
        'preguntas': preguntas,
        'respuestas_existentes': respuestas_existentes,
        'instrumento': ie.instrumento,
        'instrumento_id': ie.instrumento.id_instrumento,
    })


@login_required
def rat_responder(request, pregunta_id):
    trabajador = _get_trabajador_o_none(request)
    if not trabajador:
        return redirect('index')

    ie = _get_instrumento_empresa(request, trabajador.empresa)
    pregunta = get_object_or_404(RATPreguntas, id_rat_pregunta=pregunta_id, instrumento_empresa=ie)
    respuesta_existente = RATRespuestas.objects.filter(pregunta=pregunta, trabajador=trabajador).first()

    if request.method == 'POST':
        form = RATRespuestaForm(request.POST, instance=respuesta_existente)
        if form.is_valid():
            respuesta = form.save(commit=False)
            respuesta.pregunta = pregunta
            respuesta.trabajador = trabajador
            respuesta.save()
            return redirect(f'/rat/?instrumento_id={ie.instrumento.id_instrumento}')
    else:
        form = RATRespuestaForm(instance=respuesta_existente)

    return render(request, 'cuestionario/rat_responder.html', {
        'trabajador': trabajador,
        'pregunta': pregunta,
        'form': form,
        'editando': respuesta_existente is not None,
        'instrumento': ie.instrumento,
        'instrumento_id': ie.instrumento.id_instrumento,
    })


# ─── VISTAS COORDINADOR ───────────────────────────────────────────────────────

def _get_empresa_y_trabajador(request):
    """Devuelve (empresa, trabajador) según sea superuser o coordinador."""
    if request.user.is_superuser:
        empresa_id = request.GET.get('empresa_id') or request.session.get('empresa_id_admin')
        empresa = get_object_or_404(Empresa, id_empresa=empresa_id) if empresa_id else None
        return empresa, None
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return None, None
    return trabajador.empresa, trabajador


@login_required
def rat_panel_coordinador(request):
    empresa, trabajador = _get_empresa_y_trabajador(request)
    if not empresa:
        return redirect('index')

    ie = _get_instrumento_empresa(request, empresa)
    if not ie:
        return redirect('seleccion_instrumentos')

    preguntas = RATPreguntas.objects.filter(
        instrumento_empresa=ie
    ).prefetch_related('respuestas__trabajador')

    return render(request, 'cuestionario/rat_coordinador.html', {
        'trabajador': trabajador,
        'empresa': empresa,
        'empresa_actual': empresa,
        'preguntas': preguntas,
        'instrumento': ie.instrumento,
        'instrumento_id': ie.instrumento.id_instrumento,
    })


@login_required
def rat_nueva_pregunta(request):
    empresa, trabajador = _get_empresa_y_trabajador(request)
    if not empresa:
        return redirect('index')

    ie = _get_instrumento_empresa(request, empresa)
    if not ie:
        return redirect('seleccion_instrumentos')

    if request.method == 'POST':
        form = RATPreguntaForm(request.POST, empresa=empresa)
        if form.is_valid():
            pregunta = form.save(commit=False)
            pregunta.instrumento_empresa = ie
            pregunta.save()
            return redirect(f'/rat/coordinador/?instrumento_id={ie.instrumento.id_instrumento}')
    else:
        form = RATPreguntaForm(empresa=empresa)

    return render(request, 'cuestionario/rat_formulario.html', {
        'trabajador': trabajador,
        'empresa_actual': empresa,
        'form': form,
        'editando': False,
        'instrumento': ie.instrumento,
        'instrumento_id': ie.instrumento.id_instrumento,
    })


@login_required
def rat_editar_pregunta(request, pregunta_id):
    empresa, trabajador = _get_empresa_y_trabajador(request)
    if not empresa:
        return redirect('index')

    ie = _get_instrumento_empresa(request, empresa)
    pregunta = get_object_or_404(RATPreguntas, id_rat_pregunta=pregunta_id, instrumento_empresa=ie)

    if request.method == 'POST':
        form = RATPreguntaForm(request.POST, instance=pregunta, empresa=empresa)
        if form.is_valid():
            form.save()
            return redirect(f'/rat/coordinador/?instrumento_id={ie.instrumento.id_instrumento}')
    else:
        form = RATPreguntaForm(instance=pregunta, empresa=empresa)

    return render(request, 'cuestionario/rat_formulario.html', {
        'trabajador': trabajador,
        'empresa_actual': empresa,
        'form': form,
        'editando': True,
        'pregunta': pregunta,
        'instrumento': ie.instrumento,
        'instrumento_id': ie.instrumento.id_instrumento,
    })


@login_required
def rat_eliminar_pregunta(request, pregunta_id):
    empresa, trabajador = _get_empresa_y_trabajador(request)
    if not empresa:
        return redirect('index')

    ie = _get_instrumento_empresa(request, empresa)
    pregunta = get_object_or_404(RATPreguntas, id_rat_pregunta=pregunta_id, instrumento_empresa=ie)

    if request.method == 'POST':
        pregunta.delete()
        return redirect(f'/rat/coordinador/?instrumento_id={ie.instrumento.id_instrumento}')

    return render(request, 'cuestionario/rat_confirmar_eliminar.html', {
        'trabajador': trabajador,
        'empresa_actual': empresa,
        'pregunta': pregunta,
        'instrumento': ie.instrumento,
        'instrumento_id': ie.instrumento.id_instrumento,
    })


# ─── VERSIONES ────────────────────────────────────────────────────────────────

@login_required
def rat_versiones(request):
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    versiones = RegistroVersiones.objects.filter(
        empresa=trabajador.empresa
    ).order_by('-fecha_modificacion')

    return render(request, 'cuestionario/rat_versiones.html', {
        'trabajador': trabajador,
        'versiones': versiones,
    })


@login_required
def rat_nueva_version(request):
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    if request.method == 'POST':
        form = RegistroVersionesForm(request.POST)
        if form.is_valid():
            version = form.save(commit=False)
            version.empresa = trabajador.empresa
            version.save()
            return redirect('rat_versiones')
    else:
        form = RegistroVersionesForm()

    return render(request, 'cuestionario/rat_nueva_version.html', {
        'trabajador': trabajador,
        'form': form,
    })


@login_required
def rat_editar_version(request, version_id):
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    version = get_object_or_404(RegistroVersiones, pk=version_id, empresa=trabajador.empresa)

    if request.method == 'POST':
        form = RegistroVersionesForm(request.POST, instance=version)
        if form.is_valid():
            form.save()
            return redirect('rat_versiones')
    else:
        form = RegistroVersionesForm(instance=version)

    return render(request, 'cuestionario/rat_nueva_version.html', {
        'trabajador': trabajador,
        'form': form,
        'editando': True,
        'version': version,
    })


@login_required
def rat_eliminar_version(request, version_id):
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    version = get_object_or_404(RegistroVersiones, pk=version_id, empresa=trabajador.empresa)

    if request.method == 'POST':
        version.delete()
        return redirect('rat_versiones')

    return render(request, 'cuestionario/rat_confirmar_eliminar_version.html', {
        'trabajador': trabajador,
        'version': version,
    })


# ─── SELECCIÓN E INSTRUMENTOS ─────────────────────────────────────────────────

@login_required
def seleccion_instrumentos(request):
    if request.user.is_superuser:
        empresa_id = request.GET.get('empresa_id') or request.session.get('empresa_id_admin')
        empresa = get_object_or_404(Empresa, id_empresa=empresa_id) if empresa_id else None
        if not empresa:
            return redirect('index')
        es_coordinador = True
        trabajador = None
    else:
        trabajador = get_object_or_404(Trabajador, user=request.user)
        empresa = trabajador.empresa
        es_coordinador = trabajador.es_coordinador

    instrumentos_empresa = InstrumentoEmpresa.objects.filter(
        empresa=empresa, habilitado=True
    ).select_related('instrumento')

    instrumentos_rat   = [ie for ie in instrumentos_empresa if ie.instrumento.tipo == 'rat']
    instrumentos_otros = [ie for ie in instrumentos_empresa if ie.instrumento.tipo != 'rat']

    return render(request, 'cuestionario/seleccion_instrumentos.html', {
        'trabajador':         trabajador,
        'empresa_actual':     empresa,
        'instrumentos_rat':   instrumentos_rat,
        'instrumentos_otros': instrumentos_otros,
        'es_coordinador':     es_coordinador,
        'next_url':           request.GET.get('next'),
    })


@login_required
def rat_crear_instrumento(request):
    if request.user.is_superuser:
        empresa_id = request.GET.get('empresa_id') or request.session.get('empresa_id_admin')
        empresa = get_object_or_404(Empresa, id_empresa=empresa_id) if empresa_id else None
        if not empresa:
            return redirect('index')
    else:
        trabajador = get_object_or_404(Trabajador, user=request.user)
        if not trabajador.es_coordinador:
            return redirect('index')
        empresa = trabajador.empresa

    if request.method == 'POST':
        nombre = request.POST.get('nombre_instrumento', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if nombre:
            instrumento, _ = Instrumento.objects.get_or_create(
                nombre_instrumento=nombre,
                defaults={'descripcion': descripcion},
            )
            # get_or_create dispara la señal clonar_preguntas_rat si es nuevo
            InstrumentoEmpresa.objects.get_or_create(
                instrumento=instrumento,
                empresa=empresa,
                defaults={'habilitado': True},
            )
            next_url = request.POST.get('next', f'/instrumentos/?empresa_id={empresa.id_empresa}')
            return redirect(next_url)

    next_url = request.GET.get('next', f'/instrumentos/?empresa_id={empresa.id_empresa}')
    return render(request, 'cuestionario/rat_crear_instrumento.html', {
        'empresa': empresa,
        'next_url': next_url,
    })