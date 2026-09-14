import os
from .base import *

DEBUG = False

# --- Azure Deployment Topology ---
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allowed Hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '169.254.129.2', '*']
_azure_domain = os.environ.get('WEBSITE_HOSTNAME')
if _azure_domain:
    ALLOWED_HOSTS += [_azure_domain, f'.{_azure_domain}']
ALLOWED_HOSTS += ['.azurewebsites.net']

_custom_domain = os.environ.get('BACKEND_DOMAIN')
if _custom_domain:
    ALLOWED_HOSTS += [_custom_domain]

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = []
if _azure_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_azure_domain}')
if _custom_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_custom_domain}')
for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(','):
    origin = origin.strip()
    if origin:
        CSRF_TRUSTED_ORIGINS.append(origin)

# CORS
CORS_ALLOWED_ORIGINS = [
    o for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()
]
_frontend_url = os.environ.get('FRONTEND_URL')
if _frontend_url:
    CORS_ALLOWED_ORIGINS.append(_frontend_url)
if 'http://localhost:5173' not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append('http://localhost:5173')

# ❌ REMOVED: CORS_ALLOW_ALL_ORIGINS = True  (security risk in production)

# Security
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Database
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

# ============================================================
# LLM Configuration (Ollama + Azure OpenAI)
# ============================================================

# Ollama
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api')
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_HOST = os.environ.get('OLLAMA_HOST') or OLLAMA_BASE_URL

# Model selection
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5:1.5b')
OLLAMA_CHAT_MODEL = os.environ.get('OLLAMA_CHAT_MODEL', 'qwen2.5:1.5b')
OLLAMA_EMBED_MODEL = os.environ.get('OLLAMA_EMBED_MODEL', 'nomic-embed-text')

# Azure OpenAI (optional)
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', '')
AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY', '')
AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
AZURE_OPENAI_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')

# RAG
RAG_MIN_SIMILARITY = float(os.environ.get('RAG_MIN_SIMILARITY', '0.2'))
RAG_TOP_K = int(os.environ.get('RAG_TOP_K', '5'))

# Mock toggle
USE_MOCK_CHATBOT = os.environ.get('USE_MOCK_CHATBOT', 'False') == 'True'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'ERROR', 'propagate': True},
        'rag_langchain': {
            'handlers': ['console'],
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# ============================================================
# Azure Blob Storage
# ============================================================
USE_AZURE_STORAGE = os.environ.get('USE_AZURE_STORAGE', 'False') == 'True'

if USE_AZURE_STORAGE:
    AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
    AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')
    AZURE_CONTAINER = os.environ.get('AZURE_CONTAINER', 'media')

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.azure_storage.AzureStorage",
            "OPTIONS": {
                "account_name": AZURE_ACCOUNT_NAME,
                "account_key": AZURE_ACCOUNT_KEY,
                "azure_container": AZURE_CONTAINER,
                "overwrite_files": False,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

    MEDIA_URL = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/'