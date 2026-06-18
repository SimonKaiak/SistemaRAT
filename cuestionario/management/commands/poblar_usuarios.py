"""
management/commands/poblar_usuarios.py
--------------------------------------
Comando de gestión de Django para crear y vincular usuarios de
Django a los trabajadores existentes en la base de datos.

Uso:
    python manage.py poblar_usuarios

Comportamiento:
- Itera sobre todos los Trabajador registrados en la BD.
- Por cada trabajador usa get_or_create para crear o recuperar
  su User de Django usando el email como username.
- Si el User es nuevo (no existía), le asigna nombre, apellido y
  la contraseña por defecto de su empresa.
- Si el User ya existía, SOLO actualiza nombre/apellido — no toca
  la contraseña, para no pisar una que el trabajador ya haya
  cambiado.
- Si el trabajador no tiene User vinculado, lo asigna (sin tocar
  la contraseña de ese User si no es nuevo).
- Es seguro ejecutarlo múltiples veces: no duplica usuarios y no
  resetea contraseñas existentes.

Contraseña asignada a usuarios nuevos (generar_password_empresa,
en cuestionario/models.py): [NombreEmpresa][AñoDeCreación].
Ej: 'Mohala2026'. No depende de una lista fija de ids de empresa:
funciona automáticamente para cualquier empresa nueva.

Este comando es ejecutado automáticamente en el Start Command de
Render después de crear_admin (ver Procfile), en cada deploy.
Como ya no resetea contraseñas existentes, es seguro que corra
en cada deploy: solo provisiona a los trabajadores que aún no
tienen su User creado.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cuestionario.models import Trabajador, generar_password_empresa

class Command(BaseCommand):
    help = 'Crea y vincula usuarios de Django para trabajadores'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando vinculación de usuarios...')

        trabajadores = Trabajador.objects.select_related('empresa').all()

        creados = 0
        actualizados = 0
        for t in trabajadores:
            user, created = User.objects.get_or_create(
                username=t.email,
                defaults={
                    'email': t.email,
                    'first_name': t.nombre,
                    'last_name': f"{t.apellido_paterno} {t.apellido_materno}",
                    'is_staff': False
                }
            )

            user.first_name = t.nombre
            user.last_name = f"{t.apellido_paterno} {t.apellido_materno}"
            user.is_staff = False

            if created:
                password = generar_password_empresa(t.empresa)
                user.set_password(password)

            user.save()

            if not t.user:
                t.user = user
                t.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ {t.email} → empresa {t.empresa_id} → usuario creado con password inicial"))
                creados += 1
            else:
                self.stdout.write(f"↪ {t.email} → empresa {t.empresa_id} → ya existía, password sin tocar")
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'--- Proceso finalizado. {creados} usuarios nuevos creados, {actualizados} ya existían ---'
        ))