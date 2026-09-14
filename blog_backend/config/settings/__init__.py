"""
Settings package entry point.

Automatically selects which settings module to load based on the
DJANGO_ENV environment variable (set in .env or Azure App Settings).

Priority:
    1. DJANGO_ENV=azure      → azure.py       (Azure App Service)
    2. DJANGO_ENV=production → production.py  (generic production)
    3. default               → development.py (local dev)
"""

import os

_env = os.environ.get("DJANGO_ENV", "development").lower().strip()

if _env == "azure":
    from .azure import *          # noqa: F401,F403
elif _env in ("production", "prod"):
    from .production import *     # noqa: F401,F403
else:
    from .development import *    # noqa: F401,F403