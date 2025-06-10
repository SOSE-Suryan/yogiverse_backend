from constants import PROJECT_ENV

import os

from django.core.asgi import get_asgi_application

if PROJECT_ENV == 0:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'SOSE_backend.settings.dev')

# if PROJECT_ENV == 1:
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE',
#                           'SOSE_backend.settings.prod')


http_app = get_asgi_application()
