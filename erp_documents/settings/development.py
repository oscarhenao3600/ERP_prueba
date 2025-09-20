# Configuración de desarrollo para el sistema ERP de gestión de documentos

from .base import *

# Debug mode habilitado para desarrollo
DEBUG = True

# Configuración de base de datos para desarrollo
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuración de CORS más permisiva para desarrollo
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Configuración de logging más detallada para desarrollo
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['documents']['level'] = 'DEBUG'
LOGGING['loggers']['companies']['level'] = 'DEBUG'

# Configuración de email para desarrollo (consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuración de archivos estáticos para desarrollo
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Configuración de media files para desarrollo
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Configuración de Django Debug Toolbar (opcional)
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
    except ImportError:
        pass

# Configuración de cloud storage para desarrollo (usar bucket de prueba)
AWS_STORAGE_BUCKET_NAME = 'erp-documents-dev'
AWS_S3_REGION_NAME = 'us-east-1'

# Configuración de URLs pre-firmadas más cortas para desarrollo
PRESIGNED_URL_EXPIRATION = 1800  # 30 minutos

# Configuración de tamaño de archivo más pequeño para desarrollo
MAX_FILE_SIZE = 5242880  # 5MB

# Configuración de cache en memoria para desarrollo
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
