from django.urls import path
from .views import *


urlpatterns = [
    path('chats/', ChatAPI.as_view(), name='chats'),
    path('chats/<uuid:id>/', ChatAPI.as_view(), name='chats'),
    path('read_msg/<int:id>/', ReadChatMsgAPI.as_view(), name='read_msg'),
    path('message/', MessageAPI.as_view(), name='message'),
    path('message/<int:id>/', MessageAPI.as_view(), name='message'),
    path('attachments/', ChatAttachmentAPI.as_view(), name='chat-attachments'),
    # path('fcmtoken/', FCMTokenView.as_view(), name='fcmtoken'),
    # path('chats/notifications/', NotificationChatAPI.as_view(), name='chats_notifications'),
]
