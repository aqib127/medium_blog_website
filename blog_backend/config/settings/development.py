from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

try:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

    # Exclude admin from debug toolbar
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: not request.path.startswith('/admin/'),
    }
except ImportError:
    pass

LOGGING['root']['handlers'] = ['console']