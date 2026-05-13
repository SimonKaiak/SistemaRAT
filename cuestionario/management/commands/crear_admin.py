import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Crea el superusuario admin desde variables de entorno (seguro para deploy)'

    def handle(self, *args, **kwargs):
        username = os.environ.get('DJANGO_ADMIN_USER', 'admin')
        email    = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@sistemarat.cl')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD')

        if not password:
            self.stdout.write(self.style.WARNING(
                '⚠️  Variable DJANGO_ADMIN_PASSWORD no definida. Se omite creación del admin.'
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(
                f'✅ El usuario "{username}" ya existe. No se realizaron cambios.'
            ))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            f'✅ Superusuario "{username}" creado exitosamente.'
        ))