from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django import forms
from cuestionario.models import RATPreguntas, RATRespuestas, RegistroVersiones, Trabajador, Empresa


# ─── FORMS ────────────────────────────────────────────────────────────────────

class RATRespuestaForm(forms.ModelForm):
    class Meta:
        model = RATRespuestas
        fields = ['respuesta']
        widgets = {
            'respuesta': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Escribe tu respuesta aquí...',
                'style': 'width:100%; padding:0.6em; border-radius:6px; border:1px solid #ccc; font-size:0.95em;',
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
                'class': 'form-control',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
                'placeholder': 'Ej: Gestión de nóminas y remuneraciones',
            }),
            'responsable': forms.Select(attrs={
                'class': 'form-select',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
            }),
            'categorias_datos': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
                'placeholder': 'Ej: Datos identificativos (RUT, nombre), datos económicos (sueldo, cuenta bancaria)',
            }),
            'descripcion_titulares': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
                'placeholder': 'Ej: Trabajadores y ex-trabajadores de la empresa en relación laboral vigente o finalizada',
            }),
            'finalidad_tratamiento': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
                'placeholder': 'Ej: Calcular y pagar remuneraciones, cumplir obligaciones tributarias y previsionales',
            }),
            'base_legitimidad': forms.Select(attrs={
                'class': 'form-select',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
            }),
            'periodo_conservacion': forms.NumberInput(attrs={
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;color:inherit;background:rgba(255,255,255,0.05);',
                'placeholder': 'Ej: 60  (meses)',
            }),
            'fuente_datos': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
                'placeholder': 'Ej: El propio trabajador mediante contrato de trabajo y ficha de ingreso',
            }),
            'version': forms.Select(attrs={
                'class': 'form-select',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
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
                'class': 'form-control',
                'placeholder': 'Ej: 1.0, 1.1, 2.0',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
            }),
            'motivo_modificacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe por qué se modifica esta versión...',
                'style': 'width:100%;padding:0.5em;border-radius:6px;border:1px solid #ccc;',
            }),
        }


# ─── HELPER ───────────────────────────────────────────────────────────────────

def _get_trabajador_o_none(request):
    try:
        return Trabajador.objects.get(user=request.user)
    except Trabajador.DoesNotExist:
        return None


# ─── VIEWS ────────────────────────────────────────────────────────────────────

@login_required
def rat_panel_usuario(request):
    """Vista para el trabajador: lista las preguntas RAT y permite responderlas."""
    trabajador = _get_trabajador_o_none(request)
    if not trabajador:
        return redirect('index')

    preguntas = RATPreguntas.objects.filter(empresa=trabajador.empresa)
    respuestas_existentes = {
        r.pregunta_id: r
        for r in RATRespuestas.objects.filter(trabajador=trabajador)
    }

    context = {
        'trabajador': trabajador,
        'preguntas': preguntas,
        'respuestas_existentes': respuestas_existentes,
    }
    return render(request, 'cuestionario/rat_usuario.html', context)


@login_required
def rat_responder(request, pregunta_id):
    """Vista para que el trabajador responda (o edite) una pregunta RAT."""
    trabajador = _get_trabajador_o_none(request)
    if not trabajador:
        return redirect('index')

    pregunta = get_object_or_404(RATPreguntas, id_rat_pregunta=pregunta_id, empresa=trabajador.empresa)
    respuesta_existente = RATRespuestas.objects.filter(pregunta=pregunta, trabajador=trabajador).first()

    if request.method == 'POST':
        form = RATRespuestaForm(request.POST, instance=respuesta_existente)
        if form.is_valid():
            respuesta = form.save(commit=False)
            respuesta.pregunta = pregunta
            respuesta.trabajador = trabajador
            respuesta.save()
            return redirect('rat_panel_usuario')
    else:
        form = RATRespuestaForm(instance=respuesta_existente)

    context = {
        'trabajador': trabajador,
        'pregunta': pregunta,
        'form': form,
        'editando': respuesta_existente is not None,
    }
    return render(request, 'cuestionario/rat_responder.html', context)


@login_required
def rat_panel_coordinador(request):
    """Vista del coordinador: ve todas las preguntas y respuestas de su empresa."""
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    preguntas = RATPreguntas.objects.filter(
        empresa=trabajador.empresa
    ).prefetch_related('respuestas__trabajador')

    context = {
        'trabajador': trabajador,
        'preguntas': preguntas,
    }
    return render(request, 'cuestionario/rat_coordinador.html', context)


@login_required
def rat_nueva_pregunta(request):
    """Coordinador crea una nueva pregunta RAT."""
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    if request.method == 'POST':
        form = RATPreguntaForm(request.POST, empresa=trabajador.empresa)
        if form.is_valid():
            pregunta = form.save(commit=False)
            pregunta.empresa = trabajador.empresa
            pregunta.save()
            return redirect('rat_panel_coordinador')
    else:
        form = RATPreguntaForm(empresa=trabajador.empresa)

    context = {
        'trabajador': trabajador,
        'form': form,
        'editando': False,
    }
    return render(request, 'cuestionario/rat_formulario.html', context)


@login_required
def rat_editar_pregunta(request, pregunta_id):
    """Coordinador edita una pregunta RAT existente."""
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    pregunta = get_object_or_404(RATPreguntas, id_rat_pregunta=pregunta_id, empresa=trabajador.empresa)

    if request.method == 'POST':
        form = RATPreguntaForm(request.POST, instance=pregunta, empresa=trabajador.empresa)
        if form.is_valid():
            form.save()
            return redirect('rat_panel_coordinador')
    else:
        form = RATPreguntaForm(instance=pregunta, empresa=trabajador.empresa)

    context = {
        'trabajador': trabajador,
        'form': form,
        'editando': True,
        'pregunta': pregunta,
    }
    return render(request, 'cuestionario/rat_formulario.html', context)


@login_required
def rat_eliminar_pregunta(request, pregunta_id):
    """Coordinador elimina una pregunta RAT."""
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    pregunta = get_object_or_404(RATPreguntas, id_rat_pregunta=pregunta_id, empresa=trabajador.empresa)

    if request.method == 'POST':
        pregunta.delete()
        return redirect('rat_panel_coordinador')

    context = {
        'trabajador': trabajador,
        'pregunta': pregunta,
    }
    return render(request, 'cuestionario/rat_confirmar_eliminar.html', context)


@login_required
def rat_versiones(request):
    """Lista de versiones del RAT para la empresa del coordinador."""
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    versiones = RegistroVersiones.objects.filter(
        empresa=trabajador.empresa
    ).order_by('-fecha_modificacion')

    context = {
        'trabajador': trabajador,
        'versiones': versiones,
    }
    return render(request, 'cuestionario/rat_versiones.html', context)


@login_required
def rat_nueva_version(request):
    """Coordinador registra una nueva versión."""
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')\

    if request.method == 'POST':
        form = RegistroVersionesForm(request.POST)
        if form.is_valid():
            version = form.save(commit=False)
            version.empresa = trabajador.empresa
            version.save()
            return redirect('rat_versiones')
    else:
        form = RegistroVersionesForm()

    context = {
        'trabajador': trabajador,
        'form': form,
    }
    return render(request, 'cuestionario/rat_nueva_version.html', context)

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

    context = {
        'trabajador': trabajador,
        'form': form,
        'editando': True,
        'version': version,
    }
    return render(request, 'cuestionario/rat_nueva_version.html', context)


@login_required
def rat_eliminar_version(request, version_id):
    trabajador = _get_trabajador_o_none(request)
    if not trabajador or not trabajador.es_coordinador:
        return redirect('index')

    version = get_object_or_404(RegistroVersiones, pk=version_id, empresa=trabajador.empresa)

    if request.method == 'POST':
        version.delete()
        return redirect('rat_versiones')

    context = {
        'trabajador': trabajador,
        'version': version,
    }
    return render(request, 'cuestionario/rat_confirmar_eliminar_version.html', context)