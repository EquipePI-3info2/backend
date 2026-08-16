import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv


# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Define o modo de execução da aplicação
MODE = os.getenv('MODE', 'DEVELOPMENT')

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------------
# Segurança e configuração básica
# -----------------------------------------------------------------------------

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-troque-em-producao'
)

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Desenvolvimento local + domínios gerados pela Vercel
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.vercel.app',
]

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://localhost:5173',
    'https://*.vercel.app',
]

# Nesta primeira publicação deixamos CORS liberado.
# Depois podemos restringir para o domínio definitivo do frontend.
CORS_ALLOW_ALL_ORIGINS = True

# A Vercel fica na frente do Django como proxy HTTPS
if MODE != 'DEVELOPMENT':
    SECURE_PROXY_SSL_HEADER = (
        'HTTP_X_FORWARDED_PROTO',
        'https',
    )
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# -----------------------------------------------------------------------------
# Aplicações instaladas
# -----------------------------------------------------------------------------

# IMPORTANTE:
# django.contrib.staticfiles deve permanecer antes de cloudinary_storage.
# Cloudinary é adicionado somente fora do modo DEVELOPMENT.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'django_extensions',
    'django_filters',
    'drf_spectacular',
    'rest_framework',

    'core',
    'catalog',
    'orders',
    'stock',
]


# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'app.urls'


# -----------------------------------------------------------------------------
# Templates
# -----------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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


WSGI_APPLICATION = 'app.wsgi.application'


# -----------------------------------------------------------------------------
# Banco de dados
# -----------------------------------------------------------------------------

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# -----------------------------------------------------------------------------
# Validação de senhas
# -----------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.'
        'UserAttributeSimilarityValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.'
        'MinimumLengthValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.'
        'CommonPasswordValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.'
        'NumericPasswordValidator'
    },
]


# -----------------------------------------------------------------------------
# Internacionalização
# -----------------------------------------------------------------------------

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True
USE_TZ = True


# -----------------------------------------------------------------------------
# Arquivos estáticos
# -----------------------------------------------------------------------------

STATIC_URL = '/static/'


# -----------------------------------------------------------------------------
# Arquivos de mídia
# -----------------------------------------------------------------------------

MEDIA_ENDPOINT = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

FILE_UPLOAD_PERMISSIONS = 0o640


# -----------------------------------------------------------------------------
# Storage separado por ambiente
# -----------------------------------------------------------------------------

if MODE == 'DEVELOPMENT':

    MY_IP = os.getenv(
        'MY_IP',
        '127.0.0.1'
    )

    MEDIA_URL = '/media/'

    # Desenvolvimento:
    # imagens ficam armazenadas localmente.
    STORAGES = {
        'default': {
            'BACKEND':
            'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND':
            'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

else:

    # Produção / MIGRATE:
    # imagens de produtos, kits, perfis etc. ficam no Cloudinary.
    MEDIA_URL = '/media/'

    CLOUDINARY_URL = os.getenv(
        'CLOUDINARY_URL'
    )

    STATIC_ROOT = BASE_DIR / 'staticfiles'

    # IMPORTANTE:
    # adicionamos Cloudinary DEPOIS de django.contrib.staticfiles.
    # Isso impede o pacote Cloudinary de substituir o collectstatic
    # padrão do Django.
    INSTALLED_APPS = INSTALLED_APPS + [
        'cloudinary_storage',
        'cloudinary',
    ]

    STORAGES = {
        'default': {
            'BACKEND':
            'cloudinary_storage.storage.MediaCloudinaryStorage',
        },
        'staticfiles': {
            'BACKEND':
            'whitenoise.storage.'
            'CompressedManifestStaticFilesStorage',
        },
    }


# -----------------------------------------------------------------------------
# Configurações do Django
# -----------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'


# -----------------------------------------------------------------------------
# OpenAPI / Swagger
# -----------------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    'TITLE': 'Brookiê API',
    'DESCRIPTION':
        'API do e-commerce Brookiê — cookies e brownies artesanais.',
    'VERSION': '1.0.0',
}


# -----------------------------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.'
        'JWTAuthentication',
    ),

    'DEFAULT_PAGINATION_CLASS':
        'app.pagination.CustomPagination',

    'DEFAULT_SCHEMA_CLASS':
        'drf_spectacular.openapi.AutoSchema',

    'PAGE_SIZE': 10,

    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}


# -----------------------------------------------------------------------------
# Simple JWT
# -----------------------------------------------------------------------------

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=180
    ),

    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=1
    ),

    'AUTH_HEADER_TYPES': (
        'Bearer',
    ),
}
