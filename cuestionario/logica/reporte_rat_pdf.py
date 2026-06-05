"""
reporte_rat_pdf.py
------------------
Vista para la generación del reporte PDF de respuestas RAT de todos
los trabajadores con estado Listo de una empresa.

generar_reporte_rat_pdf(request)
    Genera un PDF con resumen de respuestas por pregunta:
    - Preguntas sino  (1, 2): porcentaje Sí / No
    - Preguntas escala (3, 4): porcentaje por opción 1-5
    - Preguntas texto  (5, 6): nube de palabras

    Control de acceso:
    - Superusuario: filtra por empresa vía query param empresa_id.
    - Coordinador: solo su empresa.
    - Trabajador regular: redirige a index.
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from cuestionario.models import (
    Trabajador, Empresa, RATPreguntas, RATRespuestas, InstrumentoEmpresa
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime
from collections import Counter
import re

# wordcloud + matplotlib para generar la imagen de nube
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

STOPWORDS_ES = {
    'de', 'la', 'el', 'en', 'y', 'a', 'los', 'las', 'un', 'una',
    'que', 'del', 'se', 'con', 'por', 'para', 'es', 'su', 'al',
    'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este',
    'si', 'porque', 'esta', 'entre', 'cuando', 'muy', 'sin',
    'sobre', 'también', 'me', 'hasta', 'hay', 'donde', 'han',
    'no', 'ni', 'mi', 'te', 'nos', 'son', 'fue', 'ser', 'tiene',
    'he', 'han', 'dado', 'nos', 'así', 'e', 'u',
}


def _wordcloud_image(textos: list[str]) -> BytesIO | None:
    """Genera una nube de palabras a partir de una lista de textos.
    Devuelve BytesIO con imagen PNG o None si no hay texto."""
    texto_completo = ' '.join(textos).lower()
    palabras = re.findall(r'[a-záéíóúüñ]{2,}', texto_completo)
    palabras_filtradas = [p for p in palabras if p not in STOPWORDS_ES]
    if not palabras_filtradas:
        return None
    frecuencias = Counter(palabras_filtradas)
    wc = WordCloud(
        width=700, height=300,
        background_color='white',
        colormap='tab10',
        max_words=80,
    ).generate_from_frequencies(frecuencias)
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf


def _tabla_sino(respuestas: list[str], styles: dict) -> list:
    """Devuelve elementos ReportLab para pregunta Sí/No."""
    total = len(respuestas)
    if total == 0:
        return [Paragraph("Sin respuestas.", styles['normal'])]
    si = sum(1 for r in respuestas if r.strip().lower() in ('si', 'sí', '1', 'true'))
    no = total - si
    pct_si = si / total * 100
    pct_no = no / total * 100

    data = [
        ['Respuesta', 'Cantidad', 'Porcentaje'],
        ['Sí', str(si), f'{pct_si:.1f}%'],
        ['No', str(no), f'{pct_no:.1f}%'],
        ['Total', str(total), '100%'],
    ]
    t = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#5e42a6')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND',    (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME',      (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
    ]))
    return [t]


def _tabla_escala(respuestas: list[str], styles: dict) -> list:
    """Devuelve elementos ReportLab para pregunta de escala 1-5."""
    total = len(respuestas)
    if total == 0:
        return [Paragraph("Sin respuestas.", styles['normal'])]
    conteo = Counter()
    for r in respuestas:
        try:
            v = int(r.strip())
            if 1 <= v <= 5:
                conteo[v] += 1
        except ValueError:
            pass

    data = [['Opción', 'Cantidad', 'Porcentaje']]
    for opcion in range(1, 6):
        cant = conteo.get(opcion, 0)
        pct = cant / total * 100 if total else 0
        data.append([str(opcion), str(cant), f'{pct:.1f}%'])
    data.append(['Total', str(total), '100%'])

    t = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#5e42a6')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND',    (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME',      (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
    ]))
    return [t]


# ──────────────────────────────────────────────
# Vista principal
# ──────────────────────────────────────────────

@login_required
def generar_reporte_rat_pdf(request):
    # ── Control de acceso ──────────────────────
    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
            empresa_obj = trabajador_actual.empresa
        except Trabajador.DoesNotExist:
            return redirect('index')
    else:
        trabajador_actual = None
        empresa_id = request.GET.get('empresa_id')
        empresa_obj = None
        if empresa_id:
            try:
                empresa_obj = Empresa.objects.get(id_empresa=empresa_id)
            except Empresa.DoesNotExist:
                return HttpResponse("Empresa no encontrada.", status=404)

    if not empresa_obj:
        return HttpResponse("No se especificó empresa.", status=400)

    # ── Instrumento RAT activo ─────────────────
    ie = InstrumentoEmpresa.objects.filter(
        empresa=empresa_obj, habilitado=True, instrumento__tipo='rat'
    ).first()
    if not ie:
        return HttpResponse("No hay instrumento RAT habilitado para esta empresa.", status=404)

    # ── Preguntas (excluyendo presentación) ────
    preguntas = ie.preguntas.exclude(
        tipo='texto', actividad_tratamiento__startswith='Presentación'
    ).exclude(
        actividad_tratamiento__icontains='Fuente de la cual provienen'
    ).order_by('id_rat_pregunta')

    if not preguntas.exists():
        return HttpResponse("No hay preguntas RAT configuradas.", status=404)

    # ── Trabajadores con RAT listo ─────────────
    total_preguntas = preguntas.count()
    trabajadores_empresa = Trabajador.objects.filter(empresa=empresa_obj)
    trabajadores_listos = []
    for t in trabajadores_empresa:
        respondidas = RATRespuestas.objects.filter(
                    trabajador=t, pregunta__instrumento_empresa=ie
                ).exclude(
                    pregunta__tipo='texto',
                    pregunta__actividad_tratamiento__startswith='Presentación'
                ).exclude(
                    pregunta__actividad_tratamiento__icontains='Fuente de la cual provienen'
                ).values('pregunta').distinct().count()
        if total_preguntas > 0 and respondidas >= total_preguntas:
            trabajadores_listos.append(t)

    if not trabajadores_listos:
        return HttpResponse("No hay trabajadores con RAT completado.", status=404)

    # ── Estilos ────────────────────────────────
    styles_rl = getSampleStyleSheet()
    style_title = ParagraphStyle(
        'RATTitle', parent=styles_rl['Heading1'],
        fontSize=18, textColor=colors.HexColor('#5e42a6'),
        spaceAfter=20, alignment=TA_CENTER,
    )
    style_portada = ParagraphStyle(
        'RATPortada', parent=styles_rl['Heading1'],
        fontSize=22, textColor=colors.HexColor('#5e42a6'),
        spaceAfter=16, alignment=TA_CENTER,
    )
    style_sub = ParagraphStyle(
        'RATSub', parent=styles_rl['Normal'],
        fontSize=12, textColor=colors.HexColor('#333333'),
        spaceAfter=8, alignment=TA_CENTER,
    )
    style_pregunta = ParagraphStyle(
        'RATPregunta', parent=styles_rl['Normal'],
        fontSize=11, textColor=colors.HexColor('#5e42a6'),
        fontName='Helvetica-Bold',
        spaceAfter=6, spaceBefore=16,
    )
    style_normal = ParagraphStyle(
        'RATNormal', parent=styles_rl['Normal'],
        fontSize=10, spaceAfter=4,
    )
    helper_styles = {'normal': style_normal}

    # ── Construcción del PDF ───────────────────
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    elements = []

    # Portada
    elements.append(Spacer(1, 1.5 * inch))
    elements.append(Paragraph(f"{ie.instrumento.nombre_instrumento}", style_portada))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(
        f"Reporte de Respuestas {ie.instrumento.nombre_instrumento}", style_sub
    ))
    elements.append(Paragraph(
        f"Empresa: {empresa_obj.nombre_empresa}", style_sub
    ))
    elements.append(Paragraph(
        f"Colaboradores con RAT completado: {len(trabajadores_listos)}", style_sub
    ))
    elements.append(Paragraph(
        f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_sub
    ))
    elements.append(Spacer(1, 2 * inch))

    from reportlab.platypus import PageBreak
    from cuestionario.models import Departamento

    def _agregar_preguntas(elements, preguntas, trabajadores_filtrados, helper_styles, style_pregunta, style_normal):
        for idx, pregunta in enumerate(preguntas, 1):
            elements.append(Paragraph(f"{idx}. {pregunta.actividad_tratamiento}", style_pregunta))
            respuestas = list(RATRespuestas.objects.filter(
                pregunta=pregunta,
                trabajador__in=trabajadores_filtrados,
            ).values_list('respuesta', flat=True))
            if pregunta.tipo == 'sino':
                elements += _tabla_sino(respuestas, helper_styles)
            elif pregunta.tipo == 'escala':
                elements += _tabla_escala(respuestas, helper_styles)
            elif pregunta.tipo == 'texto':
                img_buf = _wordcloud_image(respuestas)
                if img_buf:
                    elements.append(RLImage(img_buf, width=5.5 * inch, height=2.4 * inch))
                else:
                    elements.append(Paragraph("Sin respuestas de texto.", style_normal))
            elements.append(Spacer(1, 0.3 * inch))

    # ── Resumen Global ─────────────────────────
    elements.append(Paragraph("Resumen Global — Todos los Departamentos", style_title))
    elements.append(Spacer(1, 0.2 * inch))
    _agregar_preguntas(elements, preguntas, trabajadores_listos, helper_styles, style_pregunta, style_normal)

    # ── Por Departamento ───────────────────────
    departamentos = Departamento.objects.filter(empresa=empresa_obj)
    for depto in departamentos:
        trabajadores_depto = [t for t in trabajadores_listos if t.departamento == depto]
        if not trabajadores_depto:
            continue
        elements.append(PageBreak())
        elements.append(Paragraph(
            f"Resumen Departamento — {depto.nombre_departamento} ({len(trabajadores_depto)} colaborador{'es' if len(trabajadores_depto) > 1 else ''})",
            style_title
        ))
        elements.append(Spacer(1, 0.2 * inch))
        _agregar_preguntas(elements, preguntas, trabajadores_depto, helper_styles, style_pregunta, style_normal)

    # ── Generar PDF ────────────────────────────
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    nombre_archivo = (
        f"reporte_rat_{empresa_obj.nombre_empresa.replace(' ', '_')}"
        f"_{datetime.now().strftime('%Y%m%d')}.pdf"
    )
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    return response