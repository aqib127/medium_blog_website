import os
from .base import *

DEBUG = False

# --- Azure Deployment Topology ---
# Azure App Service terminates TLS at its proxy and forwards plain HTTP to gunicorn.
# Without this, SECURE_SSL_REDIRECT loops on every request
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allowed Hosts - Azure domain + custom domain
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
_azure_domain = os.environ.get('WEBSITE_HOSTNAME')
if _azure_domain:
    ALLOWED_HOSTS += [_azure_domain, f'.{_azure_domain}']

_custom_domain = os.environ.get('BACKEND_DOMAIN')
if _custom_domain:
    ALLOWED_HOSTS += [_custom_domain]

CSRF_TRUSTED_ORIGINS = []
if _azure_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_azure_domain}')
if _custom_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_custom_domain}')
for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(','):
    origin = origin.strip()
    if origin:
        CSRF_TRUSTED_ORIGINS.append(origin)

# CORS: React frontend runs on a separate origin
CORS_ALLOWED_ORIGINS = [
    o for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()
]
_frontend_url = os.environ.get('FRONTEND_URL')
if _frontend_url:
    CORS_ALLOWED_ORIGINS.append(_frontend_url)
if 'http://localhost:5173' not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append('http://localhost:5173')

# Serve static files via WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Security Headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database - PostgreSQL with pgvector
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Azure Blob Storage for media files
if os.environ.get('USE_AZURE_STORAGE', 'False') == 'True':
    AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
    AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')
    AZURE_CONTAINER = os.environ.get('AZURE_CONTAINER', 'media')
    
    STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'

# Ollama Configuration
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama2')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}