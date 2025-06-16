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

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import chat_app.routing  # create this file

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Yogiverse.settings.dev')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_app.routing.websocket_urlpatterns
        )
    ),
})
