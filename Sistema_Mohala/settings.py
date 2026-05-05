import os
from pathlib import Path
import dj_database_url
import pymysql # <--- AGREGADO: Para compatibilidad con Python 3.13

# AGREGADO: Parche para que Django reconozca el driver en Railway
pymysql.install_as_MySQLdb()

# Rutas base
BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY y DEBUG
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-yw8ipn#h#l*3rau(91-_*@hou*2ra=wkota3mriwczp8pupd=i')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Dominios permitidos (Actualizado para V2)
ALLOWED_HOSTS = ['*'] # <--- Simplificado para evitar errores de dominio en el despliegue

# Confianza explícita para CSRF (Actualizado para V2)
CSRF_TRUSTED_ORIGINS = [
    'https://mohalav2-production.up.railway.app',
    'https://*.railway.app'
]

# Aplicaciones (Tu app es cuestionario)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cuestionario',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Sistema_Mohala.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Sistema_Mohala.wsgi.application'

# --- 🗄️ BASE DE DATOS (Corregida para evitar Timeout en V2) ---
MYSQL_URL = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')

if MYSQL_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            MYSQL_URL,
            conn_max_age=0, 
            ssl_require=False
        )
    }
    # Forzamos el motor de MySQL
    DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'mohala',
            'USER': 'root',
            'PASSWORD': '53176_Ben101',
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }

# Idioma y hora (Tu ajuste a Santiago)
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Seguridad adicional
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'