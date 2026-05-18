from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from cuestionario.models import Trabajador, Empresa, Departamento, NivelJerarquico, Cargo
import openpyxl


@login_required
@require_POST
def cargar_usuarios_excel(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)

    empresa_id = request.POST.get('empresa_id')
    archivo = request.FILES.get('archivo')

    if not archivo or not empresa_id:
        return JsonResponse({'ok': False, 'error': 'Faltan datos'})

    try:
        empresa = Empresa.objects.get(id_empresa=empresa_id)
    except Empresa.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Empresa no encontrada'})

    try:
        wb = openpyxl.load_workbook(archivo)
        ws = wb.active
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Archivo Excel inválido'})

    creados = 0
    omitidos = []

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):
            continue

        try:
            rut        = str(row[0]).strip() if row[0] else ''
            nombre     = str(row[1]).strip() if row[1] else ''
            ap_paterno = str(row[2]).strip() if row[2] else ''
            ap_materno = str(row[3]).strip() if row[3] else ''
            email      = str(row[4]).strip() if row[4] else ''
            genero     = str(row[5]).strip() if row[5] else 'M'
            depto_nom  = str(row[6]).strip() if row[6] else ''
            nivel_nom  = str(row[7]).strip() if row[7] else ''
            cargo_nom  = str(row[8]).strip() if row[8] else ''
        except IndexError:
            omitidos.append(f'Fila {i}: faltan columnas')
            continue

        if not all([rut, nombre, ap_paterno, ap_materno, email, depto_nom, nivel_nom, cargo_nom]):
            omitidos.append(f'Fila {i}: campos incompletos')
            continue

        if Trabajador.objects.filter(rut=rut).exists():
            omitidos.append(f'Fila {i} ({nombre}): RUT {rut} ya existe')
            continue

        username = email.split('@')[0]

        if User.objects.filter(username=username).exists():
            omitidos.append(f'Fila {i} ({nombre}): usuario {username} ya existe')
            continue

        if User.objects.filter(email=email).exists():
            omitidos.append(f'Fila {i} ({nombre}): email {email} ya existe')
            continue

        try:
            depto  = Departamento.objects.get(nombre_departamento__iexact=depto_nom, empresa=empresa)
            nivel  = NivelJerarquico.objects.get(nombre_nivel_jerarquico__iexact=nivel_nom, empresa=empresa)
            cargo  = Cargo.objects.get(nombre_cargo__iexact=cargo_nom, empresa=empresa)
        except (Departamento.DoesNotExist, NivelJerarquico.DoesNotExist, Cargo.DoesNotExist) as e:
            omitidos.append(f'Fila {i} ({nombre}): {str(e)}')
            continue

        try:
            new_user = User.objects.create_user(username=username, email=email, password='Mohala2026')
            t = Trabajador(
                rut=rut, nombre=nombre,
                apellido_paterno=ap_paterno, apellido_materno=ap_materno,
                email=email, genero=genero, es_coordinador=False,
                empresa=empresa, nivel_jerarquico=nivel,
                cargo=cargo, departamento=depto,
                user=new_user,
            )
            Trabajador.objects.bulk_create([t])
            creados += 1
        except Exception as e:
            omitidos.append(f'Fila {i} ({nombre}): {str(e)}')

    return JsonResponse({
        'ok': True,
        'creados': creados,
        'omitidos': omitidos,
    })