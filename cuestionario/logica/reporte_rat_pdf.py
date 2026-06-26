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

    Incluye portada institucional (logo placeholder, metadatos),
    encabezado con empresa + instrumento y pie de página con
    número de página y aviso de confidencialidad en cada hoja.

    Control de acceso:
    - Superusuario: filtra por empresa vía query param empresa_id.
    - Coordinador: solo su empresa.
    - Trabajador regular: redirige a index.

    Filtra por instrumento vía query param instrumento_id (RAT 1,
    RAT 2, etc.). Si no se especifica, usa el primer instrumento
    RAT habilitado de la empresa (ordenado por id).
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from cuestionario.models import (
    Trabajador, Empresa, RATPreguntas, RATRespuestas, InstrumentoEmpresa, Departamento
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image as RLImage, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String
from io import BytesIO
from datetime import datetime
from collections import Counter, OrderedDict
import re

# wordcloud + matplotlib para generar la imagen de nube
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


# ──────────────────────────────────────────────
# Paleta institucional
# ──────────────────────────────────────────────

COLOR_MARCA = colors.HexColor('#5e42a6')
COLOR_GRIS = colors.HexColor('#6b6b6b')
COLOR_LINEA = colors.HexColor('#dddddd')


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


# ──────────────────────────────────────────────
# Gráficos de avance (equivalentes a los de
# Chart.js de la página de Seguimiento RAT, pero
# renderizados como imagen estática con matplotlib
# para poder insertarlos en el PDF).
# ──────────────────────────────────────────────

COLOR_LISTOS = '#27ae60'
COLOR_PENDIENTES = '#e67e22'


def _grafico_pie_avance(listos: int, pendientes: int) -> BytesIO:
    """Gráfico de torta Total de Trabajadores: Listos vs Pendientes."""
    valores = [listos, pendientes]
    total = sum(valores)

    def _autopct(pct):
        if pct <= 0:
            return ''
        cantidad = round(pct * total / 100.0)
        return f'{cantidad} ({pct:.0f}%)'

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        valores,
        labels=['Terminados', 'Pendientes'],
        colors=[COLOR_LISTOS, COLOR_PENDIENTES],
        autopct=_autopct,
        textprops={'fontsize': 11},
        startangle=90,
    )
    ax.set_title('Total de Trabajadores', fontsize=13, fontweight='bold', color='#333333')
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf


def _grafico_pie_respuestas(conteo: Counter, titulo: str, label_map: dict | None = None) -> BytesIO | None:
    """Gráfico de torta para distribución de respuestas de una pregunta."""
    if not conteo:
        return None
    label_map = label_map or {}
    etiquetas = [label_map.get(k, k) for k in conteo.keys()]
    valores = list(conteo.values())
    total = sum(valores)

    def _autopct(pct):
        if pct <= 0:
            return ''
        cantidad = round(pct * total / 100.0)
        return f'{cantidad} ({pct:.0f}%)'

    colores = ['#5e42a6', '#27ae60', '#e67e22', '#3498db', '#c0392b', '#f1c40f', '#1abc9c', '#e91e63']
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(
        valores,
        labels=etiquetas,
        colors=colores[:len(valores)],
        autopct=_autopct,
        textprops={'fontsize': 9},
        startangle=90,
    )
    ax.set_title(titulo, fontsize=12, fontweight='bold', color='#333333')
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf


def _grafico_barras_avance(datos: OrderedDict, titulo: str) -> BytesIO:
    """Gráfico de barras Listos/Pendientes agrupado por la clave de
    `datos` (departamento o nivel jerárquico)."""
    etiquetas = list(datos.keys())
    listos = [v['terminados'] for v in datos.values()]
    pendientes = [v['pendientes'] for v in datos.values()]
    posiciones = range(len(etiquetas))
    ancho_barra = 0.35

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.bar([p - ancho_barra / 2 for p in posiciones], listos, width=ancho_barra,
           label='Terminados', color=COLOR_LISTOS)
    ax.bar([p + ancho_barra / 2 for p in posiciones], pendientes, width=ancho_barra,
           label='Pendientes', color=COLOR_PENDIENTES)
    ax.set_xticks(list(posiciones))
    ax.set_xticklabels(etiquetas, rotation=15, ha='right', fontsize=9)
    ax.set_ylabel('Trabajadores')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_title(titulo, fontsize=13, fontweight='bold', color='#333333')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.32), ncol=2, frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf


COLOR_ESCALA = ['#c0392b', '#e67e22', '#f1c40f', '#3498db', '#27ae60']  # 1..5
COLOR_NO = '#c0392b'  # rojo para "No" en preguntas sino (distinto del naranjo de Listos/Pendientes)


def _normalizar_respuesta_grafico(valor: str, tipo: str):
    """Convierte la respuesta cruda en la etiqueta que se usa como serie del gráfico."""
    if tipo == 'sino':
        return 'Sí' if valor.strip().lower() in ('si', 'sí', '1', 'true') else 'No'
    if tipo == 'escala':
        try:
            v = int(valor.strip())
            if 1 <= v <= 5:
                return v
        except ValueError:
            pass
    return None


def _grafico_pregunta_por_nivel(respuestas_qs, tipo: str, niveles_referencia: list) -> BytesIO | None:
    """Distribución de respuestas de una pregunta (sino/escala), separada
    por nivel jerárquico. Usa barras APILADAS (una barra por nivel,
    segmentada por opción) en vez de barras agrupadas, para evitar que
    las preguntas de escala (5 opciones) multipliquen la cantidad de
    barras al cruzarse con los niveles jerárquicos.

    `niveles_referencia` es la misma lista de niveles que usa el gráfico
    de avance "Por Nivel Jerárquico", para que un nivel sin respuestas
    en esta pregunta puntual siga apareciendo con barra en 0 en vez de
    desaparecer del gráfico."""
    conteo_por_nivel = OrderedDict((nivel, Counter()) for nivel in niveles_referencia)
    for r in respuestas_qs:
        opcion = _normalizar_respuesta_grafico(r.respuesta, tipo)
        if opcion is None:
            continue
        nivel = (
            r.trabajador.nivel_jerarquico.nombre_nivel_jerarquico
            if r.trabajador.nivel_jerarquico_id else 'Sin Nivel'
        )
        conteo_por_nivel.setdefault(nivel, Counter())
        conteo_por_nivel[nivel][opcion] += 1

    if not any(conteo_por_nivel.values()):
        return None

    if tipo == 'sino':
        opciones, colores = ['Sí', 'No'], [COLOR_LISTOS, COLOR_NO]
    else:
        opciones, colores = [1, 2, 3, 4, 5], COLOR_ESCALA

    niveles = list(conteo_por_nivel.keys())
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    base = [0] * len(niveles)
    for opcion, color in zip(opciones, colores):
        valores = [conteo_por_nivel[n].get(opcion, 0) for n in niveles]
        if not any(valores):
            continue
        barras = ax.bar(niveles, valores, bottom=base, label=str(opcion), color=color)
        for barra, valor in zip(barras, valores):
            if valor > 0:
                ax.text(
                    barra.get_x() + barra.get_width() / 2,
                    barra.get_y() + barra.get_height() / 2,
                    str(valor),
                    ha='center', va='center', fontsize=9.5,
                    fontweight='bold', color='#1a1a1a',
                )
        base = [b + v for b, v in zip(base, valores)]

    ax.set_ylabel('Trabajadores')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_title('Por Nivel Jerárquico', fontsize=13, fontweight='bold', color='#333333')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=min(len(opciones), 5), frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, transparent=True)
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
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_MARCA),
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
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_MARCA),
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


CATEGORIAS_LABELS = {
    'contactabilidad': 'Datos de contactabilidad de personas',
    'bancarios': 'Datos bancarios o finanzas personales',
    'historia_clinica': 'Datos de historia clínica de personas',
    'otra_categoria': 'Otra categoría',
}


def _tabla_generica(respuestas: list[str], styles: dict, label_map: dict | None = None) -> list:
    """Tabla de frecuencias genérica para tipos de pregunta que no tienen
    un formato propio (periodo, select_categorias, listado_usuarios, etc.).
    Cuenta cuántas veces se repite cada respuesta exacta."""
    total = len(respuestas)
    if total == 0:
        return [Paragraph("Sin respuestas.", styles['normal'])]

    label_map = label_map or {}
    conteo = Counter(r.strip() for r in respuestas if r and r.strip())
    if not conteo:
        return [Paragraph("Sin respuestas.", styles['normal'])]

    style_celda = ParagraphStyle('celdaGenerica', fontSize=9.5, leading=12)
    data = [['Respuesta', 'Cantidad', 'Porcentaje']]
    for valor, cant in conteo.most_common():
        etiqueta = label_map.get(valor, valor)
        pct = cant / total * 100
        data.append([Paragraph(etiqueta, style_celda), str(cant), f'{pct:.1f}%'])
    data.append(['Total', str(total), '100%'])

    t = Table(data, colWidths=[4.5 * inch, 1.0 * inch, 1.0 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_MARCA),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN',         (0, 0), (0, -1),  'LEFT'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9.5),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND',    (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME',      (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
    ]))
    return [t]


def _logo_placeholder(ancho=2.6 * inch, alto=0.9 * inch) -> Drawing:
    """Genera un recuadro placeholder centrado con el texto 'LOGO EMPRESA',
    para usar en la portada mientras no se cargue un logo real."""
    d = Drawing(ancho, alto)
    d.hAlign = 'CENTER'
    rect = Rect(0, 0, ancho, alto, fillColor=colors.white, strokeColor=COLOR_GRIS, strokeWidth=1)
    rect.strokeDashArray = [4, 3]
    d.add(rect)
    d.add(String(ancho / 2, alto / 2 - 5, "LOGO EMPRESA", fontSize=13, fillColor=COLOR_GRIS,
                  textAnchor='middle', fontName='Helvetica-Bold'))
    return d


def _hacer_header_footer(empresa_obj, instrumento_nombre):
    """Devuelve una función onPage para ReportLab que dibuja un
    encabezado institucional (a partir de la página 2) y un pie de
    página con número de página y aviso de confidencialidad en
    todas las hojas."""
    def _dibujar(canvas, doc):
        ancho, alto = A4
        canvas.saveState()

        # ── Pie de página (todas las hojas) ──
        canvas.setStrokeColor(COLOR_LINEA)
        canvas.setLineWidth(0.6)
        canvas.line(2 * cm, 1.5 * cm, ancho - 2 * cm, 1.5 * cm)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(COLOR_GRIS)
        canvas.drawString(2 * cm, 1.05 * cm, f"Sistema RAT — {empresa_obj.nombre_empresa}")
        canvas.drawCentredString(ancho / 2, 1.05 * cm, "Documento confidencial — uso interno")
        canvas.drawRightString(ancho - 2 * cm, 1.05 * cm, f"Página {canvas.getPageNumber()}")

        # ── Encabezado (a partir de la 2ª página, la portada no lo lleva) ──
        if canvas.getPageNumber() > 1:
            canvas.setFont('Helvetica-Bold', 10)
            canvas.setFillColor(COLOR_MARCA)
            canvas.drawString(2 * cm, alto - 1.4 * cm, empresa_obj.nombre_empresa)
            canvas.setFont('Helvetica', 9)
            canvas.setFillColor(COLOR_GRIS)
            canvas.drawRightString(ancho - 2 * cm, alto - 1.4 * cm, instrumento_nombre)
            canvas.setStrokeColor(COLOR_MARCA)
            canvas.setLineWidth(1.1)
            canvas.line(2 * cm, alto - 1.55 * cm, ancho - 2 * cm, alto - 1.55 * cm)

        canvas.restoreState()
    return _dibujar


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
    instrumento_id = request.GET.get('instrumento_id')
    ie_qs = InstrumentoEmpresa.objects.filter(
        empresa=empresa_obj, habilitado=True, instrumento__tipo='rat'
    )
    if instrumento_id:
        ie_qs = ie_qs.filter(instrumento__id_instrumento=instrumento_id)
    ie = ie_qs.order_by('instrumento__id_instrumento').first()
    if not ie:
        return HttpResponse("No hay instrumento RAT habilitado para esta empresa.", status=404)

    # ── Preguntas (excluyendo presentación) ────
    preguntas = ie.preguntas.exclude(
        tipo='texto', actividad_tratamiento__startswith='Presentación'
    ).order_by('id_rat_pregunta')

    if not preguntas.exists():
        return HttpResponse("No hay preguntas RAT configuradas.", status=404)

    # ── Trabajadores con RAT listo / pendiente ─
    total_preguntas = preguntas.count()
    trabajadores_empresa = Trabajador.objects.filter(empresa=empresa_obj).select_related('departamento', 'nivel_jerarquico')
    trabajadores_terminados = []
    trabajadores_pendientes = []
    datos_departamento = OrderedDict()
    datos_nivel = OrderedDict()
    for t in trabajadores_empresa:
        respondidas = RATRespuestas.objects.filter(
                    trabajador=t, pregunta__instrumento_empresa=ie
                ).exclude(
                    pregunta__tipo='texto',
                    pregunta__actividad_tratamiento__startswith='Presentación'
                ).values('pregunta').distinct().count()
        listo = total_preguntas > 0 and respondidas >= total_preguntas

        nombre_departamento = t.departamento.nombre_departamento if t.departamento_id else 'Sin Departamento'
        nombre_nivel = t.nivel_jerarquico.nombre_nivel_jerarquico if t.nivel_jerarquico_id else 'Sin Nivel'
        datos_departamento.setdefault(nombre_departamento, {'terminados': 0, 'pendientes': 0})
        datos_nivel.setdefault(nombre_nivel, {'terminados': 0, 'pendientes': 0})

        if listo:
            trabajadores_terminados.append(t)
            datos_departamento[nombre_departamento]['terminados'] += 1
            datos_nivel[nombre_nivel]['terminados'] += 1
        else:
            trabajadores_pendientes.append(t)
            datos_departamento[nombre_departamento]['pendientes'] += 1
            datos_nivel[nombre_nivel]['pendientes'] += 1

    if not trabajadores_terminados:
        return HttpResponse("No hay trabajadores con RAT Terminado.", status=404)

    # ── Estilos ────────────────────────────────
    styles_rl = getSampleStyleSheet()
    style_title = ParagraphStyle(
        'RATTitle', parent=styles_rl['Heading1'],
        fontSize=16, textColor=COLOR_MARCA,
        spaceAfter=18, alignment=TA_CENTER,
    )
    style_portada = ParagraphStyle(
        'RATPortada', parent=styles_rl['Heading1'],
        fontSize=24, textColor=COLOR_MARCA,
        spaceAfter=6, alignment=TA_CENTER,
    )
    style_sub = ParagraphStyle(
        'RATSub', parent=styles_rl['Normal'],
        fontSize=12, textColor=colors.HexColor('#333333'),
        spaceAfter=8, alignment=TA_CENTER,
    )
    style_confidencial = ParagraphStyle(
        'RATConfidencial', parent=styles_rl['Normal'],
        fontSize=9, textColor=COLOR_GRIS,
        alignment=TA_CENTER,
    )
    style_pregunta = ParagraphStyle(
        'RATPregunta', parent=styles_rl['Normal'],
        fontSize=11, textColor=COLOR_MARCA,
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
        topMargin=2.3 * cm, bottomMargin=2.3 * cm,
    )
    elements = []

    # ── Portada institucional ──────────────────
    elements.append(Spacer(1, 1 * inch))
    elements.append(_logo_placeholder())
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"{ie.instrumento.nombre_instrumento}", style_portada))
    elements.append(Paragraph("Reporte de Respuestas", style_sub))
    elements.append(Spacer(1, 0.6 * inch))

    metadata = [
        ['Empresa', empresa_obj.nombre_empresa],
        ['Colaboradores con RAT Terminado', str(len(trabajadores_terminados))],
        ['Colaboradores con RAT Pendiente', str(len(trabajadores_pendientes))],
        ['Total de Colaboradores', str(len(trabajadores_terminados) + len(trabajadores_pendientes))],
        ['Fecha de generación', datetime.now().strftime('%d/%m/%Y %H:%M')],
    ]
    t_meta = Table(metadata, colWidths=[2.8 * inch, 2.8 * inch])
    t_meta.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (0, 0), (0, -1), COLOR_MARCA),
        ('TEXTCOLOR',     (1, 0), (1, -1), colors.HexColor('#333333')),
        ('FONTSIZE',      (0, 0), (-1, -1), 10.5),
        ('TOPPADDING',    (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LINEBELOW',     (0, 0), (-1, -2), 0.6, COLOR_LINEA),
        ('ALIGN',         (0, 0), (0, -1), 'LEFT'),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 1.8 * inch))
    elements.append(Paragraph("Este documento contiene información sensible de la empresa.", style_confidencial))
    elements.append(Paragraph("Su distribución debe restringirse a personal autorizado.", style_confidencial))

    elements.append(PageBreak())

    # ── Resumen Gráfico de Avance ───────────────
    elements.append(Paragraph("Resumen Gráfico de Avance", style_title))
    elements.append(Spacer(1, 0.15 * inch))

    img_pie = _grafico_pie_avance(len(trabajadores_terminados), len(trabajadores_pendientes))
    elements.append(RLImage(img_pie, width=2.3 * inch, height=2.3 * inch, hAlign='CENTER'))
    elements.append(Spacer(1, 0.2 * inch))

    img_departamento = _grafico_barras_avance(datos_departamento, 'Por Departamento')
    elements.append(RLImage(img_departamento, width=5.4 * inch, height=2.7 * inch, hAlign='CENTER'))
    elements.append(Spacer(1, 0.15 * inch))

    img_nivel = _grafico_barras_avance(datos_nivel, 'Por Nivel Jerárquico')
    elements.append(RLImage(img_nivel, width=5.4 * inch, height=2.7 * inch, hAlign='CENTER'))

    elements.append(PageBreak())

    # Misma lista de niveles que usa el gráfico de avance de arriba, para
    # que las preguntas 1-4 muestren siempre los mismos niveles jerárquicos.
    niveles_ordenados = list(datos_nivel.keys())

    def _agregar_preguntas(elements, preguntas, trabajadores_filtrados, helper_styles, style_pregunta, style_normal, niveles_ordenados):
        for idx, pregunta in enumerate(preguntas, 1):
            elements.append(Paragraph(f"{idx}. {pregunta.actividad_tratamiento}", style_pregunta))
            respuestas_qs = RATRespuestas.objects.filter(
                pregunta=pregunta,
                trabajador__in=trabajadores_filtrados,
            ).select_related('trabajador__nivel_jerarquico')
            respuestas = [r.respuesta for r in respuestas_qs]
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
            elif pregunta.tipo == 'select_categorias':
                elements += _tabla_generica(respuestas, helper_styles, label_map=CATEGORIAS_LABELS)
            else:
                # periodo, listado_usuarios y cualquier otro tipo futuro
                elements += _tabla_generica(respuestas, helper_styles)

            # Gráfico de pie para preguntas con orden 1, 2, 3, 6, 9
            if idx in (1, 2, 3, 6, 9) and respuestas:
                ACTIVIDAD_LABELS_CORTO = {
                    'Limpieza, depuración de datos': 'Limpieza/depuración',
                    'Combinación de datos con otra fuente': 'Combinación de datos',
                    'Uso operacional (para llamar, enviar emails, mensajes de texto, Whatsapp)': 'Uso operacional\n(llamar, emails, Whatsapp)',
                    'Otra actividad': 'Otra actividad',
                }
                if pregunta.tipo == 'select_categorias':
                    label_map = CATEGORIAS_LABELS
                elif pregunta.tipo == 'select_actividad':
                    label_map = ACTIVIDAD_LABELS_CORTO
                else:
                    label_map = {}
                conteo_pie = Counter(r.strip() for r in respuestas if r and r.strip())
                # Para listado_usuarios expandir por comas
                if pregunta.tipo == 'listado_usuarios':
                    conteo_pie = Counter()
                    for r in respuestas:
                        for nombre in r.split(','):
                            nombre = nombre.strip()
                            if nombre:
                                conteo_pie[nombre] += 1
                img_pie_preg = _grafico_pie_respuestas(conteo_pie, f'Distribución — {pregunta.actividad_tratamiento[:40]}', label_map=label_map)
                if img_pie_preg:
                    elements.append(Spacer(1, 0.15 * inch))
                    elements.append(RLImage(img_pie_preg, width=4.5 * inch, height=3.5 * inch, hAlign='CENTER'))

            # Gráfico adicional separado por nivel jerárquico (solo preguntas 1 a 4)
            if idx <= 4 and pregunta.tipo in ('sino', 'escala'):
                img_nivel_pregunta = _grafico_pregunta_por_nivel(respuestas_qs, pregunta.tipo, niveles_ordenados)
                if img_nivel_pregunta:
                    elements.append(Spacer(1, 0.15 * inch))
                    elements.append(RLImage(img_nivel_pregunta, width=5.4 * inch, height=2.7 * inch, hAlign='CENTER'))

            elements.append(Spacer(1, 0.3 * inch))

    # ── Resumen Global ─────────────────────────
    elements.append(Paragraph("Resumen Global — Todos los Departamentos", style_title))
    elements.append(Spacer(1, 0.2 * inch))
    _agregar_preguntas(elements, preguntas, trabajadores_terminados, helper_styles, style_pregunta, style_normal, niveles_ordenados)

    # ── Por Departamento ───────────────────────
    departamentos = Departamento.objects.filter(empresa=empresa_obj)
    for depto in departamentos:
        trabajadores_depto = [t for t in trabajadores_terminados if t.departamento == depto]
        if not trabajadores_depto:
            continue
        elements.append(PageBreak())
        elements.append(Paragraph(
            f"Resumen Departamento — {depto.nombre_departamento} ({len(trabajadores_depto)} colaborador{'es' if len(trabajadores_depto) > 1 else ''})",
            style_title
        ))
        elements.append(Spacer(1, 0.2 * inch))
        _agregar_preguntas(elements, preguntas, trabajadores_depto, helper_styles, style_pregunta, style_normal, niveles_ordenados)

    # ── Generar PDF ────────────────────────────
    pagina = _hacer_header_footer(empresa_obj, ie.instrumento.nombre_instrumento)
    doc.build(elements, onFirstPage=pagina, onLaterPages=pagina)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    nombre_archivo = (
        f"reporte_{ie.instrumento.nombre_instrumento.replace(' ', '_')}"
        f"_{empresa_obj.nombre_empresa.replace(' ', '_')}"
        f"_{datetime.now().strftime('%Y%m%d')}.pdf"
    )
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    return response