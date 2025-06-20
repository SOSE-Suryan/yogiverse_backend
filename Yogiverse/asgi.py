from constants import PROJECT_ENV
import os

if PROJECT_ENV == 0:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'Yogiverse.settings.dev')

# if PROJECT_ENV == 1:
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE',
#                           'SOSE_backend.settings.prod')


# http_app = get_asgi_application()

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from chat_app.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})