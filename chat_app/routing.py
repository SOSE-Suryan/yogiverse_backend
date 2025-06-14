from django.urls import re_path, path
from .consumer import TestConsumer

websocket_urlpatterns = [
    # re_path(r'ws/discuss/(?P<chat_id>[0-9A-Fa-f-]+)', AsyncChatConsumer.as_asgi()),
    
    re_path(r'ws/test/$',TestConsumer.as_asgi())
]
