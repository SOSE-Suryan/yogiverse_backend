from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

# Register your models here.


@admin.register(ChatModel)
class ChatModelAdmin(ImportExportModelAdmin):
    list_display = ("is_single_chat", "created_by",
                    "created_on", "group_name", "chat_id", "id")[::-1]
    filter_horizontal = ("members",)


@admin.register(MessageModel)
class MessageModelAdmin(ImportExportModelAdmin):

    list_display = ("files_attachment", "reply_message", "message",
                    "sent_at", "sender", "is_read", "chat", "id")[::-1]
    ordering = ('-sent_at',)
    search_fields = ("message", "id")


@admin.register(ChatAttachmentModel)
class ChatAttachmentModelAdmin(ImportExportModelAdmin):
    list_display = ("sent_at", "attachment", "chat", "sender", "id")[::-1]


@admin.register(FCMTokenModel)
class FCMTokenModelAdmin(admin.ModelAdmin):
    list_display = ('device_type', 'employee', 'token', 'created_on', )
