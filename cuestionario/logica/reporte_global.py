"""
reporte_global.py
------------------------
Vistas para la generación y visualización del reporte global de
evaluaciones de desempeño en formato PDF.
Accesible por superusuarios y coordinadores de empresa.

generar_reporte_global_pdf(request)
    Genera un PDF con el reporte consolidado de todos los trabajadores
    de una empresa que tengan evaluaciones completadas.

    Control de acceso:
    - Superusuario: filtra por empresa vía query param empresa_id.
    - Coordinador: genera solo el reporte de su propia empresa.
    - Trabajador regular: redirige a index.

    Proceso:
    1. Crea un registro ReporteGlobal temporal con contenido vacío
       para obtener un ID antes de generar el PDF.
    2. Genera una portada con: título, ID de reporte, empresa,
       total de colaboradores, fecha y período.
    3. Por cada trabajador con resultados consolidados genera una
       sección con:
       - Tabla de información personal (cargo, nivel, jefe, timestamps).
       - Por cada dimensión una tabla con: código, competencia,
         indicador, puntaje autoevaluación, puntaje jefe y diferencia.
       - Colores alternados por dimensión (verde/azul).
       - Separador PageBreak entre trabajadores.
    4. Guarda el PDF generado en el campo contenido_pdf del
       ReporteGlobal y lo devuelve como respuesta inline.

    Estilos:
    - Color corporativo #5e42a6 en encabezados de tablas y título.
    - Verde (#51ff85) para primera dimensión, azul (#2196F3) para
      las siguientes.
    - Diferencia positiva con prefijo '+', negativa sin prefijo.

ver_reporte_global_pdf(request, reporte_id)
    Recupera y devuelve inline un ReporteGlobal ya generado por su ID.
    El coordinador solo puede ver reportes de su propia empresa.
    Devuelve 404 si el reporte no existe o no tiene PDF guardado.
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from cuestionario.models import (Trabajador, Autoevaluacion, EvaluacionJefatura, ResultadoConsolidado, ReporteGlobal, TextosEvaluacion, Empresa)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape
from collections import OrderedDict


@login_required
def generar_reporte_global_pdf(request):
    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
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

    # Coordinador solo puede generar reporte de su empresa
    if trabajador_actual:
        empresa_obj = trabajador_actual.empresa

    trabajadores_qs = Trabajador.objects.filter(
        resultadoconsolidado__isnull=False
    ).select_related(
        'cargo',
        'nivel_jerarquico',
        'id_jefe_directo',
        'empresa'
    ).distinct()

    if empresa_obj:
        trabajadores_qs = trabajadores_qs.filter(empresa=empresa_obj)

    trabajadores = trabajadores_qs.order_by('apellido_paterno', 'nombre')

    if not trabajadores.exists():
        return HttpResponse("No hay trabajadores con evaluaciones completadas.", status=404)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'GlobalTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#5e42a6'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    portada_style = ParagraphStyle(
        'GlobalPortada',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#5e42a6'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'GlobalHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#51ff85'),
        spaceAfter=12,
        spaceBefore=20
    )
    func_heading_style = ParagraphStyle(
        'GlobalFuncHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2196F3'),
        spaceAfter=12,
        spaceBefore=20
    )
    comp_style = ParagraphStyle(
        'GlobalCompStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#51ff85'),
        fontName='Helvetica-Bold',
        spaceAfter=2,
    )
    comp_func_style = ParagraphStyle(
        'GlobalCompFuncStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2196F3'),
        fontName='Helvetica-Bold',
        spaceAfter=2,
    )
    indicator_style = ParagraphStyle(
        'GlobalIndicatorStyle',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#555555'),
        leading=9,
    )

    reporte_global_temp = ReporteGlobal.objects.create(
        contenido_pdf=b'',
        total_trabajadores=trabajadores.count(),
        periodo=2026,
        empresa=empresa_obj
    )

    # PORTADA
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("REPORTE GLOBAL DE EVALUACIONES DE DESEMPEÑO", portada_style))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"ID Reporte: #{reporte_global_temp.id_reporte_global}", title_style))
    if empresa_obj:
        elements.append(Paragraph(f"Empresa: {empresa_obj.nombre_empresa}", title_style))
    elements.append(Paragraph(f"Total de Colaboradores: {trabajadores.count()}", title_style))
    elements.append(Paragraph(f"Fecha de Generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", title_style))
    elements.append(Paragraph("Periodo: 2026", title_style))
    elements.append(PageBreak())

    total = trabajadores.count()

    for idx, trabajador in enumerate(trabajadores, 1):

        empresa = trabajador.empresa

        resultados = ResultadoConsolidado.objects.filter(
            trabajador=trabajador
        ).order_by('textos_evaluacion_codigo_excel')

        if not resultados.exists():
            continue

        codigos = list(resultados.values_list('textos_evaluacion_codigo_excel', flat=True).distinct())
        textos_qs = TextosEvaluacion.objects.filter(
            empresa=empresa,
            codigo_excel__in=codigos
        ).select_related('dimension', 'competencia')
        textos_map = {t.codigo_excel: t for t in textos_qs}

        dims_ordenadas = {}
        for r in resultados:
            texto_eval = textos_map.get(r.textos_evaluacion_codigo_excel)
            if not texto_eval:
                continue
            r.texto_eval = texto_eval
            dim_id = texto_eval.dimension.id_dimension
            dim_nombre = texto_eval.dimension.nombre_dimension
            if dim_id not in dims_ordenadas:
                dims_ordenadas[dim_id] = {'nombre': dim_nombre, 'items': []}
            dims_ordenadas[dim_id]['items'].append(r)

        resultados_por_dim = OrderedDict(
            (v['nombre'], sorted(v['items'], key=lambda x: x.texto_eval.id_textos_evaluacion))
            for k, v in sorted(dims_ordenadas.items())
        )

        auto = Autoevaluacion.objects.filter(
            trabajador=trabajador, estado_finalizacion=True
        ).first()
        jefe = EvaluacionJefatura.objects.filter(
            trabajador_evaluado=trabajador, estado_finalizacion=True
        ).first()

        timestamp_auto = auto.momento_evaluacion.strftime("%d/%m/%Y %H:%M") if auto else "Pendiente"
        timestamp_jefe = jefe.momento_evaluacion.strftime("%d/%m/%Y %H:%M") if jefe else "N/A"

        elements.append(
            Paragraph(f"Reporte de Evaluación de Desempeño — #{idx} de {total}", title_style)
        )
        elements.append(Spacer(1, 0.2 * inch))

        jefe_directo_nombre = (
            f"{trabajador.id_jefe_directo.nombre} "
            f"{trabajador.id_jefe_directo.apellido_paterno} "
            f"{trabajador.id_jefe_directo.apellido_materno}"
            if trabajador.id_jefe_directo else "N/A"
        )

        info_data = [
            ['Colaborador:',                    f"{trabajador.nombre} {trabajador.apellido_paterno} {trabajador.apellido_materno}"],
            ['Empresa:',                        trabajador.empresa.nombre_empresa],
            ['Cargo:',                          trabajador.cargo.nombre_cargo],
            ['Nivel:',                          trabajador.nivel_jerarquico.nombre_nivel_jerarquico],
            ['Jefatura Directa:',               jefe_directo_nombre],
            ['Autoevaluación finalizada:',      timestamp_auto],
            ['Evaluación Jefatura finalizada:', timestamp_jefe],
        ]

        info_table = Table(info_data, colWidths=[2.5 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR',     (0, 0), (-1, -1), colors.black),
            ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME',      (0, 0), (0, -1),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))

        for dim_idx, (dim_nombre, lista) in enumerate(resultados_por_dim.items()):
            dim_heading = heading_style if dim_idx == 0 else func_heading_style
            dim_comp_style = comp_style if dim_idx == 0 else comp_func_style

            elements.append(Paragraph(f"Dimensión: {dim_nombre}", dim_heading))

            dim_data = [['Código', 'Competencia / Indicador', 'AutoEv', 'Ev. Jefe', 'Diferencia']]
            for r in lista:
                celda = [
                    Paragraph(escape(r.texto_eval.competencia.nombre_competencia), dim_comp_style),
                    Paragraph(escape(r.texto_eval.texto), indicator_style),
                ]
                dim_data.append([
                    r.texto_eval.codigo_excel,
                    celda,
                    str(r.puntaje_autoev),
                    str(r.puntaje_jefe) if r.puntaje_jefe > 0 else 'N/A',
                    f"{'+' if r.diferencia > 0 else ''}{int(r.diferencia)}",
                ])

            dim_table = Table(dim_data, colWidths=[0.7 * inch, 3.2 * inch, 0.7 * inch, 0.7 * inch, 0.8 * inch])
            dim_table.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#5e42a6')),
                ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN',         (1, 0), (1, -1),  'LEFT'),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('VALIGN',        (1, 1), (1, -1),  'TOP'),
                ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0), (-1, 0),  10),
                ('FONTSIZE',      (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING',    (0, 0), (-1, -1), 6),
                ('GRID',          (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(dim_table)
            elements.append(Spacer(1, 0.3 * inch))

        if idx < total:
            elements.append(PageBreak())

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    reporte_global_temp.contenido_pdf = pdf_bytes
    reporte_global_temp.save()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="reporte_respuestas_global_{reporte_global_temp.id_reporte_global}.pdf"'
    )
    return response


@login_required
def ver_reporte_global_pdf(request, reporte_id):
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
        reporte = ReporteGlobal.objects.get(id_reporte_global=reporte_id)
    except ReporteGlobal.DoesNotExist:
        return HttpResponse("Reporte no encontrado", status=404)

    # Coordinador solo puede ver reportes de su empresa
    if trabajador_actual and reporte.empresa != trabajador_actual.empresa:
        return redirect('index')

    if not reporte.contenido_pdf:
        return HttpResponse("Este reporte no tiene PDF generado", status=404)

    response = HttpResponse(reporte.contenido_pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_respuestas_global_{reporte_id}.pdf"'
    return response