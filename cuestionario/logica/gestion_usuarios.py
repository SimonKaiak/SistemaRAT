"""
gestion_usuarios.py
--------------------------
Vistas para la gestión administrativa de usuarios y trabajadores.
Solo accesible por superusuarios (devuelve 403 o redirige en caso contrario).

Vistas:

panel_gestion_usuarios(request)
    Muestra el panel de gestión con la lista de coordinadores y
    trabajadores de la empresa seleccionada. La empresa se obtiene
    por query param o desde la sesión. Template: gestion_usuarios.html

agregar_coordinador(request, trabajador_id)
    Marca a un trabajador como coordinador (es_coordinador=True).
    Responde JSON {ok, error}.

quitar_coordinador(request, trabajador_id)
    Quita el rol de coordinador a un trabajador (es_coordinador=False).
    Responde JSON {ok, error}.

modificar_usuario(request, trabajador_id)
    Actualiza los datos de un trabajador vía JSON en el body:
    nombre, apellidos, email, RUT, género, coordinador,
    departamento, nivel jerárquico y cargo.
    Si cambia el email, actualiza también el User de Django asociado.
    Valida que el nuevo RUT no esté duplicado.
    Responde JSON {ok, nombre_completo, email}.

resetear_clave(request, trabajador_id)
    Resetea la contraseña del usuario asociado al trabajador a
    'Mohala2026' y envía un correo de notificación al trabajador.
    Si el correo falla, igual devuelve ok=True pero indica
    correo_enviado=False con el detalle del error.
    Responde JSON {ok, correo_enviado}.

eliminar_usuario_panel(request, trabajador_id)
    Elimina el Trabajador y su User de Django asociado.
    Responde JSON {ok, error}.

crear_usuario_panel(request)
    Crea un nuevo Trabajador y su User de Django vía JSON en el body.
    Valida RUT, username y email duplicados.
    Asigna nivel jerárquico, cargo y departamento verificando que
    pertenezcan a la empresa indicada.
    Contraseña inicial: 'Mohala2026'.
    Si falla la creación del Trabajador, elimina el User creado
    para evitar usuarios huérfanos.
    Responde JSON {ok, id, nombre_completo, email, departamento}.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from cuestionario.models import Empresa, Trabajador, RATRespuestas, InstrumentoEmpresa, generar_password_empresa
import json


@login_required
def panel_gestion_usuarios(request):
    if not request.user.is_superuser:
        return redirect('index')

    empresa_id = request.GET.get('empresa_id') or request.session.get('empresa_id_admin')
    empresa_seleccionada = None

    if empresa_id:
        empresa_seleccionada = Empresa.objects.filter(id_empresa=empresa_id).first()
        request.session['empresa_id_admin'] = empresa_id

    coordinadores = []
    trabajadores = []

    if empresa_seleccionada:
        coordinadores = Trabajador.objects.filter(
            empresa=empresa_seleccionada,
            es_coordinador=True
        ).select_related('user', 'departamento', 'cargo', 'nivel_jerarquico')

        trabajadores = Trabajador.objects.filter(
            empresa=empresa_seleccionada,
            es_coordinador=False
        ).select_related('user', 'departamento', 'cargo', 'nivel_jerarquico')
        
    context = {
        'es_admin_sistema': True,
        'nombre_usuario': request.user.username,
        'empresa_seleccionada': empresa_seleccionada,
        'empresas_activas': Empresa.objects.filter(empresa_activa=True),
        'coordinadores': coordinadores,
        'trabajadores': trabajadores,
    }
    return render(request, 'cuestionario/gestion_usuarios.html', context)


@login_required
@require_POST
def agregar_coordinador(request, trabajador_id):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        t = Trabajador.objects.get(pk=trabajador_id)
        t.es_coordinador = True
        t.save()
        return JsonResponse({'ok': True})
    except Trabajador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Trabajador no encontrado'})


@login_required
@require_POST
def quitar_coordinador(request, trabajador_id):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        t = Trabajador.objects.get(pk=trabajador_id)
        t.es_coordinador = False
        t.save()
        return JsonResponse({'ok': True})
    except Trabajador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Trabajador no encontrado'})


@login_required
@require_POST
def modificar_usuario(request, trabajador_id):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        data = json.loads(request.body)
        t = Trabajador.objects.get(pk=trabajador_id)
        t.nombre = data.get('nombre', t.nombre).strip()
        t.apellido_paterno = data.get('apellido_paterno', t.apellido_paterno).strip()
        t.apellido_materno = data.get('apellido_materno', t.apellido_materno).strip()
        nuevo_email = data.get('email', t.email).strip()

        if nuevo_email != t.email and t.user:
            t.user.username = nuevo_email
            t.user.email = nuevo_email
            t.user.save()
            t.email = nuevo_email

        nuevo_rut = data.get('rut', '').strip()
        if nuevo_rut and nuevo_rut != t.rut:
            if Trabajador.objects.filter(rut=nuevo_rut).exclude(pk=t.pk).exists():
                return JsonResponse({'ok': False, 'error': f'Ya existe un trabajador con RUT {nuevo_rut}'})
            t.rut = nuevo_rut

        from cuestionario.models import Departamento, NivelJerarquico, Cargo
        t.genero = data.get('genero', t.genero)
        t.es_coordinador = data.get('es_coordinador', t.es_coordinador)

        depto_id = data.get('departamento_id')
        nivel_id = data.get('nivel_id')
        cargo_id = data.get('cargo_id')
        if depto_id:
            try:
                t.departamento = Departamento.objects.get(id_departamento=depto_id)
            except Departamento.DoesNotExist:
                pass
        if nivel_id:
            try:
                t.nivel_jerarquico = NivelJerarquico.objects.get(id_nivel_jerarquico=nivel_id)
            except NivelJerarquico.DoesNotExist:
                pass
        if cargo_id:
            try:
                t.cargo = Cargo.objects.get(id_cargo=cargo_id)
            except Cargo.DoesNotExist:
                pass

        t.save()
        return JsonResponse({
            'ok': True,
            'nombre_completo': f"{t.nombre} {t.apellido_paterno}",
            'email': t.email,
        })
    except Trabajador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Trabajador no encontrado'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})


@login_required
@require_POST
def resetear_clave(request, trabajador_id):
    if not request.user.is_superuser:
        try:
            trabajador_sesion = Trabajador.objects.get(user=request.user)
            if not trabajador_sesion.es_coordinador:
                return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
        except Trabajador.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        t = Trabajador.objects.get(pk=trabajador_id)
        if not t.user:
            return JsonResponse({'ok': False, 'error': 'El trabajador no tiene usuario asociado'})

        nueva_clave = generar_password_empresa(t.empresa)
        t.user.set_password(nueva_clave)
        t.user.save()

        try:
            send_mail(
                subject='Restablecimiento de contraseña — Sistema RAT',
                message=(
                    f"Hola {t.nombre} {t.apellido_paterno},\n\n"
                    f"Tu contraseña en el Sistema RAT ha sido restablecida por un administrador.\n\n"
                    f"  Usuario: {t.email}\n"
                    f"  Contraseña: {nueva_clave}\n\n"
                    f"Te recomendamos iniciar sesión y cambiar tu contraseña a la brevedad.\n\n"
                    f"Sistema RAT — {t.empresa.nombre_empresa}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[t.email],
                fail_silently=True,
            )
        except Exception:
            pass

        empresa_id = t.empresa.id_empresa
        return redirect(f'/seguimiento/rat/?empresa_id={empresa_id}')

    except Trabajador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Trabajador no encontrado'})


@login_required
@require_POST
def eliminar_usuario_panel(request, trabajador_id):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        t = Trabajador.objects.get(pk=trabajador_id)
        if t.user:
            t.user.delete()
        t.delete()
        return JsonResponse({'ok': True})
    except Trabajador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Trabajador no encontrado'})


@login_required
@require_POST
def crear_usuario_panel(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    try:
        from cuestionario.models import Departamento, NivelJerarquico, Cargo
        data = json.loads(request.body)

        empresa = Empresa.objects.get(id_empresa=data.get('empresa_id'))
        rut        = data.get('rut', '').strip()
        nombre     = data.get('nombre', '').strip()
        ap_paterno = data.get('apellido_paterno', '').strip()
        ap_materno = data.get('apellido_materno', '').strip()
        email      = data.get('email', '').strip()
        genero     = data.get('genero', 'M').strip()
        es_coord   = data.get('es_coordinador', False)
        nivel_id   = data.get('nivel_id')
        cargo_id   = data.get('cargo_id')
        depto_id   = data.get('departamento_id')

        if not all([rut, nombre, ap_paterno, ap_materno, email, nivel_id, cargo_id, depto_id]):
            return JsonResponse({'ok': False, 'error': 'Todos los campos son obligatorios'})

        if Trabajador.objects.filter(rut=rut).exists():
            return JsonResponse({'ok': False, 'error': f'Ya existe un trabajador con RUT {rut}'})

        username = email.split('@')[0]

        if User.objects.filter(username=username).exists():
            return JsonResponse({'ok': False, 'error': f'Ya existe un usuario con username {username}'})

        if User.objects.filter(email=email).exists():
            return JsonResponse({'ok': False, 'error': f'Ya existe un usuario con email {email}'})

        nivel      = NivelJerarquico.objects.get(id_nivel_jerarquico=nivel_id, empresa=empresa)
        cargo      = Cargo.objects.get(id_cargo=cargo_id, empresa=empresa)
        departamento = Departamento.objects.get(id_departamento=depto_id, empresa=empresa)

        clave_inicial = generar_password_empresa(empresa)
        new_user = User.objects.create_user(username=username, email=email, password=clave_inicial)

        try:
            t = Trabajador(
                rut=rut, nombre=nombre,
                apellido_paterno=ap_paterno, apellido_materno=ap_materno,
                email=email, genero=genero, es_coordinador=es_coord,
                empresa=empresa, nivel_jerarquico=nivel,
                cargo=cargo, departamento=departamento,
                user=new_user,
            )
            Trabajador.objects.bulk_create([t])
            t_creado = Trabajador.objects.get(rut=rut)
        except Exception as e:
            new_user.delete()
            raise e

        return JsonResponse({
            'ok': True,
            'id': t_creado.id_trabajador,
            'nombre_completo': f"{t_creado.nombre} {t_creado.apellido_paterno}",
            'email': t_creado.email,
            'departamento': t_creado.departamento.nombre_departamento,
        })
    except Empresa.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Empresa no encontrada'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})
    

@login_required
@require_POST
def resetear_clave_seguimiento(request, trabajador_id):
    """Reset de clave llamado desde seguimiento_rat. Redirige de vuelta."""
    if not request.user.is_superuser:
        try:
            trabajador_sesion = Trabajador.objects.get(user=request.user)
            if not trabajador_sesion.es_coordinador:
                return redirect('index')
        except Trabajador.DoesNotExist:
            return redirect('index')
    try:
        t = Trabajador.objects.get(pk=trabajador_id)
        if t.user:
            nueva_clave = generar_password_empresa(t.empresa)
            t.user.set_password(nueva_clave)
            t.user.save()
            try:
                send_mail(
                    subject='Restablecimiento de contraseña — Sistema RAT',
                    message=(
                        f"Hola {t.nombre} {t.apellido_paterno},\n\n"
                        f"Tu contraseña en el Sistema RAT ha sido restablecida por un administrador.\n\n"
                        f"  Usuario: {t.email}\n"
                        f"  Contraseña: {nueva_clave}\n\n"
                        f"Te recomendamos iniciar sesión y cambiar tu contraseña a la brevedad.\n\n"
                        f"Sistema RAT — {t.empresa.nombre_empresa}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[t.email],
                    fail_silently=True,
                )
            except Exception:
                pass
    except Trabajador.DoesNotExist:
        pass
    empresa_id = request.POST.get('empresa_id', '')
    return redirect(f'/seguimiento/rat/?empresa_id={empresa_id}')


@login_required
@require_POST
def enviar_recordatorio_rat(request, trabajador_id):
    """Envía correo de recordatorio RAT. Redirige de vuelta al seguimiento."""
    if not request.user.is_superuser:
        try:
            trabajador_sesion = Trabajador.objects.get(user=request.user)
            if not trabajador_sesion.es_coordinador:
                return redirect('index')
        except Trabajador.DoesNotExist:
            return redirect('index')
    try:
        t = Trabajador.objects.get(pk=trabajador_id)
        nombre_rat = request.POST.get('nombre_rat', 'RAT')
        try:
            send_mail(
                subject=f'Recordatorio: {nombre_rat} pendiente — Sistema RAT',
                message=(
                    f"Estimad@ {t.nombre} {t.apellido_paterno},\n\n"
                    f"Te recordamos que tienes pendiente completar el {nombre_rat} "
                    f"en el Sistema RAT de {t.empresa.nombre_empresa}.\n\n"
                    f"Por favor ingresa al sistema a la brevedad para completarlo.\n\n"
                    f"Sistema RAT — {t.empresa.nombre_empresa}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[t.email],
                fail_silently=True,
            )
        except Exception:
            pass
    except Trabajador.DoesNotExist:
        pass
    empresa_id = request.POST.get('empresa_id', '')
    return redirect(f'/seguimiento/rat/?empresa_id={empresa_id}')


@login_required
@require_POST
def resetear_respuestas_rat(request, trabajador_id):
    if not request.user.is_superuser:
        try:
            trabajador_sesion = Trabajador.objects.get(user=request.user)
            if not trabajador_sesion.es_coordinador:
                return redirect('index')
        except Trabajador.DoesNotExist:
            return redirect('index')

    empresa_id = request.POST.get('empresa_id', '')

    try:
        t = Trabajador.objects.get(pk=trabajador_id)
        instrumento_empresa_rat = InstrumentoEmpresa.objects.filter(
            empresa=t.empresa, habilitado=True, instrumento__tipo='rat'
        ).first()

        if instrumento_empresa_rat:
            total_preguntas = instrumento_empresa_rat.preguntas.exclude(
                tipo='texto', actividad_tratamiento__startswith='Presentación'
            ).exclude(
                actividad_tratamiento__icontains='Fuente de la cual provienen'
            ).count()
            respondidas = RATRespuestas.objects.filter(
                trabajador=t, pregunta__instrumento_empresa=instrumento_empresa_rat
            ).exclude(
                pregunta__tipo='texto', pregunta__actividad_tratamiento__startswith='Presentación'
            ).exclude(
                pregunta__actividad_tratamiento__icontains='Fuente de la cual provienen'
            ).values('pregunta').distinct().count()
            rat_listo = total_preguntas > 0 and respondidas >= total_preguntas

            if rat_listo:
                RATRespuestas.objects.filter(
                    trabajador=t, pregunta__instrumento_empresa=instrumento_empresa_rat
                ).delete()

    except Trabajador.DoesNotExist:
        pass

    return redirect(f'/seguimiento/rat/?empresa_id={empresa_id}')