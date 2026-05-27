"""
gemini_admin.py
----------------
Vistas para la integración con Gemini AI, permitiendo crear prompts,
generar informes en PDF y gestionar el historial de consultas.
Accesible por superusuarios y coordinadores de empresa.

Configuración:
- Carga la API key de Gemini desde variables de entorno (GEMINI_API_KEY).
- Modelo activo: gemini-2.5-flash (modificable en generar_informe_gemini).

Vistas:

panel_gemini(request)
    Muestra el panel principal de Gemini con el historial de prompts
    (últimos 20) y el último prompt generado para la empresa activa.
    Superusuario filtra por empresa vía query param; coordinador
    ve solo su empresa. Template: gemini_admin.html

editar_prompt(request)
    Crea un nuevo PromptGemini a partir del texto enviado por POST.
    El coordinador solo puede crear prompts de su propia empresa.
    Redirige al panel tras guardar.

generar_informe_gemini(request, prompt_id)
    Genera un informe PDF a partir de un prompt existente usando
    la API de Gemini. Si el PDF ya existe lo devuelve directamente.
    Proceso:
    1. Recopila documentos de la Biblioteca (estado_carga=True)
       y el último ReporteGlobal de la empresa como contexto.
    2. Envía todo a Gemini y obtiene la respuesta en texto.
    3. Construye el PDF con ReportLab (título, fecha, empresa,
       prompt usado e informe generado) con estilos personalizados.
    4. Guarda el PDF en el campo archivo_pdf del PromptGemini.
    5. Devuelve el PDF como respuesta HTTP inline.
    En caso de error muestra una página HTML con el detalle.

ver_informe_gemini(request, prompt_id)
    Muestra el informe de un prompt. Si tiene PDF guardado lo
    devuelve directamente. Si solo tiene texto, lo renderiza como
    HTML con formato básico e indica que se genere el PDF completo.

eliminar_prompt(request, prompt_id)
    Elimina un PromptGemini via POST. Redirige al panel tras borrar.

listar_modelos(request)
    Solo superusuario. Lista todos los modelos Gemini disponibles
    con la API key que soporten generateContent. Útil para depuración
    y para saber qué modelo usar en generar_informe_gemini.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from cuestionario.models import PromptGemini, Biblioteca, ReporteGlobal, Empresa, Trabajador
import google.generativeai as genai
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


@login_required
def panel_gemini(request):
    es_coordinador = False
    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
            es_coordinador = True
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
            pass

    # Coordinador siempre ve su empresa
    if es_coordinador:
        empresa_obj = trabajador_actual.empresa

    if empresa_obj:
        ultimo_prompt = PromptGemini.objects.filter(empresa=empresa_obj).first()
        historial = PromptGemini.objects.filter(empresa=empresa_obj)[:20]
    else:
        ultimo_prompt = PromptGemini.objects.first()
        historial = PromptGemini.objects.all()[:20]

    context = {
        'ultimo_prompt': ultimo_prompt,
        'historial': historial,
        'empresas': Empresa.objects.filter(empresa_activa=True),
        'empresa_actual': empresa_obj,
        'es_coordinador': es_coordinador,
    }

    return render(request, 'cuestionario/gemini_admin.html', context)


@login_required
def editar_prompt(request):
    es_coordinador = False
    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
            es_coordinador = True
        except Trabajador.DoesNotExist:
            return redirect('index')
    else:
        trabajador_actual = None

    if request.method == 'POST':
        prompt_texto = request.POST.get('prompt_texto', '')
        empresa_id = request.POST.get('empresa_id')

        # Coordinador solo puede crear prompts de su empresa
        if es_coordinador:
            empresa_id = trabajador_actual.empresa.id_empresa

        if prompt_texto.strip():
            PromptGemini.objects.create(
                prompt_texto=prompt_texto,
                empresa_id=empresa_id if empresa_id else None
            )
            return redirect('panel_gemini')

    return redirect('panel_gemini')


@login_required
def generar_informe_gemini(request, prompt_id):
    es_coordinador = False
    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
            es_coordinador = True
        except Trabajador.DoesNotExist:
            return redirect('index')
    else:
        trabajador_actual = None

    try:
        prompt_obj = PromptGemini.objects.get(id_prompt=prompt_id)
    except PromptGemini.DoesNotExist:
        return HttpResponse("Prompt no encontrado", status=404)

    # Coordinador solo puede generar informes de su empresa
    if es_coordinador and prompt_obj.empresa != trabajador_actual.empresa:
        return redirect('index')

    if prompt_obj.archivo_pdf:
        response_http = HttpResponse(prompt_obj.archivo_pdf, content_type='application/pdf')
        response_http['Content-Disposition'] = f'inline; filename="informe_gemini_{prompt_id}.pdf"'
        return response_http

    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash') #Cambiar esta linea para cambiar modelo de Gemini

        if prompt_obj.empresa:
            docs_biblioteca = Biblioteca.objects.filter(
                estado_carga=True,
                empresa=prompt_obj.empresa
            )
            ultimo_reporte = ReporteGlobal.objects.filter(
                empresa=prompt_obj.empresa
            ).order_by('-timestamp').first()
        else:
            docs_biblioteca = Biblioteca.objects.filter(estado_carga=True)
            ultimo_reporte = ReporteGlobal.objects.order_by('-timestamp').first()

        partes = []
        for doc in docs_biblioteca:
            partes.append({'mime_type': 'application/pdf', 'data': bytes(doc.archivo)})
        if ultimo_reporte and ultimo_reporte.contenido_pdf:
            partes.append({'mime_type': 'application/pdf', 'data': bytes(ultimo_reporte.contenido_pdf)})
        partes.append(prompt_obj.prompt_texto)

        response = model.generate_content(partes)
        respuesta_texto = response.text

        prompt_obj.respuesta_gemini = respuesta_texto
        prompt_obj.pdf_generado = True
        prompt_obj.save()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch, leftMargin=1*inch, rightMargin=1*inch)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#5e42a6'),
            spaceAfter=20,
            alignment=1
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#2196F3'),
            spaceAfter=10,
            spaceBefore=15
        )

        elements.append(Paragraph("Informe Generado por Gemini AI", title_style))
        elements.append(Spacer(1, 0.2*inch))

        fecha_generacion = prompt_obj.timestamp.strftime("%d/%m/%Y %H:%M")
        elements.append(Paragraph(f"<b>Fecha de generación:</b> {fecha_generacion}", body_style))
        if prompt_obj.empresa:
            elements.append(Paragraph(f"<b>Empresa:</b> {prompt_obj.empresa.nombre_empresa}", body_style))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph("Prompt Utilizado", subtitle_style))
        prompt_escapado = prompt_obj.prompt_texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        elements.append(Paragraph(prompt_escapado, body_style))
        elements.append(Spacer(1, 0.3*inch))

        elements.append(Paragraph("Informe Generado", title_style))
        elements.append(Spacer(1, 0.1*inch))

        lineas = respuesta_texto.split('\n')
        for linea in lineas:
            if linea.strip():
                linea = linea.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                linea_limpia = linea.replace('**', '<b>').replace('**', '</b>')
                linea_limpia = linea_limpia.replace('*', '<i>').replace('*', '</i>')
                linea_limpia = linea_limpia.replace('#', '')
                try:
                    if linea.strip().startswith('##'):
                        elements.append(Paragraph(linea_limpia.strip(), subtitle_style))
                    else:
                        elements.append(Paragraph(linea_limpia, body_style))
                except Exception as e:
                    print(f"Error procesando línea: {str(e)}")
                    continue

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        prompt_obj.archivo_pdf = pdf
        prompt_obj.save()

        response_http = HttpResponse(pdf, content_type='application/pdf')
        response_http['Content-Disposition'] = f'inline; filename="informe_gemini_{prompt_id}.pdf"'
        return response_http

    except Exception as e:
        error_msg = f"ERROR al generar informe: {str(e)}"
        print(error_msg)
        prompt_obj.respuesta_gemini = error_msg
        prompt_obj.save()
        return HttpResponse(f"""
            <html>
            <body style="font-family: Arial; padding: 40px;">
                <h1 style="color: #ff5151;">Error al generar PDF</h1>
                <p><strong>Detalles del error:</strong></p>
                <pre style="background: #f0f0f0; padding: 20px; border-radius: 5px;">{error_msg}</pre>
                <br>
                <a href="/gemini/" style="background: #5e42a6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Volver al Panel Gemini</a>
            </body>
            </html>
        """, status=500)
    

@login_required
def eliminar_prompt(request, prompt_id):
    prompt = get_object_or_404(PromptGemini, id_prompt=prompt_id)
    if request.method == 'POST':
        prompt.delete()
    return redirect('panel_gemini')


@login_required
def listar_modelos(request):
    if not request.user.is_superuser:
        return redirect('index')

    try:
        modelos = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos.append(m.name)

        return HttpResponse(f"""
            <html>
            <body style="font-family: Arial; padding: 40px;">
                <h1>Modelos disponibles con tu API key:</h1>
                <ul>
                    {''.join([f'<li>{m}</li>' for m in modelos])}
                </ul>
                <br>
                <a href="/gemini/">Volver</a>
            </body>
            </html>
        """)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")


@login_required
def ver_informe_gemini(request, prompt_id):
    es_coordinador = False
    if not request.user.is_superuser:
        try:
            trabajador_actual = Trabajador.objects.get(user=request.user)
            if not trabajador_actual.es_coordinador:
                return redirect('index')
            es_coordinador = True
        except Trabajador.DoesNotExist:
            return redirect('index')
    else:
        trabajador_actual = None

    try:
        prompt_obj = PromptGemini.objects.get(id_prompt=prompt_id)
    except PromptGemini.DoesNotExist:
        return HttpResponse("Prompt no encontrado", status=404)

    # Coordinador solo puede ver informes de su empresa
    if es_coordinador and prompt_obj.empresa != trabajador_actual.empresa:
        return redirect('index')

    if prompt_obj.archivo_pdf:
        response = HttpResponse(prompt_obj.archivo_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="informe_gemini_{prompt_id}.pdf"'
        return response

    if not prompt_obj.respuesta_gemini:
        return HttpResponse("Este prompt aún no tiene informe generado. Haz click en 'Generar PDF' primero.", status=404)

    contenido = prompt_obj.respuesta_gemini
    contenido = contenido.replace('**', '<strong>').replace('**', '</strong>')
    contenido = contenido.replace('*', '<em>').replace('*', '</em>')
    contenido = contenido.replace('\n', '<br>')

    return HttpResponse(f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 900px;
                    margin: 40px auto;
                    padding: 20px;
                    line-height: 1.6;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    border-bottom: 3px solid #5e42a6;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                h1 {{
                    color: #5e42a6;
                    margin: 0;
                }}
                .meta {{
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 10px;
                }}
                .prompt {{
                    background: #f0f0f0;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 30px;
                }}
                .content {{
                    color: #333;
                }}
                .actions {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
                a {{
                    color: #5e42a6;
                    text-decoration: none;
                    padding: 10px 20px;
                    background: #5e42a6;
                    color: white;
                    border-radius: 5px;
                    display: inline-block;
                    margin-right: 10px;
                }}
                a:hover {{
                    background: #4a3285;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Informe Generado por Gemini AI</h1>
                    <div class="meta">
                        Prompt ID: #{prompt_obj.id_prompt} | 
                        Fecha: {prompt_obj.timestamp.strftime("%d/%m/%Y %H:%M")}
                    </div>
                </div>
                
                <div class="prompt">
                    <strong>Prompt utilizado:</strong><br>
                    {prompt_obj.prompt_texto}
                </div>
                
                <div class="content">
                    <h2>Informe:</h2>
                    {contenido}
                    <p style="color: #ff5151; margin-top: 20px;"><strong>Nota:</strong> Este prompt solo tiene texto guardado. Genera el PDF para ver el formato completo.</p>
                </div>
                
                <div class="actions">
                    <a href="/gemini/">← Volver al Panel</a>
                    <a href="/gemini/generar/{prompt_obj.id_prompt}/" target="_blank">📄 Generar PDF</a>
                </div>
            </div>
        </body>
        </html>
    """)