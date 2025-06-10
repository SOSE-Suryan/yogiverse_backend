"""
WSGI config for Yogiverse project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""
import os

from django.core.wsgi import get_wsgi_application
from constants import PROJECT_ENV

if PROJECT_ENV == 0:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'SOSE_backend.settings.dev')

# if PROJECT_ENV == 1:
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE',
#                           'SOSE_backend.settings.prod')

application = get_wsgi_application()
