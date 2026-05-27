"""
manejo_archivos.py
--------------------
Vista para visualizar documentos PDF almacenados en la Biblioteca.
Solo accesible por superusuarios.

ver_archivo_biblioteca(request, biblioteca_id)
    Recupera un documento de la tabla Biblioteca por su ID y lo
    devuelve como respuesta HTTP con content-type application/pdf
    para visualización inline en el navegador.
    Si el documento no existe o el usuario no es superusuario,
    redirige al index.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponse
from cuestionario.models import Biblioteca


@login_required
def ver_archivo_biblioteca(request, biblioteca_id):
    if not request.user.is_superuser:
        return redirect('index')
    try:
        doc = Biblioteca.objects.get(id_biblioteca=biblioteca_id)
    except Biblioteca.DoesNotExist:
        return redirect('index')
    response = HttpResponse(bytes(doc.archivo), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{doc.nombre}.pdf"'
    return response