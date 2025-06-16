from django.db import models

# Create your models here.
from django.db import models
from uuid import uuid4
from user_app.models import UserModel
from datetime import datetime, timedelta
from django.utils import timezone


# Create your models here.
class ChatModel(models.Model):
    chat_id = models.UUIDField(default=uuid4, editable=False, unique=True)
    members = models.ManyToManyField(UserModel)
    group_name = models.CharField(max_length=255,blank=True, null=True)
    created_on = models.DateTimeField(default=timezone.now, blank=True, null=True)
    created_by = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="created_by", blank=True, null=True)
    is_single_chat = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    # def get_members(self):
    #     return ",".join([m.user_id for m in self.members.all()])

    def __str__(self):
        return str(self.chat_id)
    
    @property
    def all_messages1(self):
        mesg = self.messages.all()
        return len(mesg)

    class Meta:
        verbose_name = 'chat'
        verbose_name_plural = 'chats'


class ChatAttachmentModel(models.Model):
    sender = models.ForeignKey(UserModel, on_delete=models.CASCADE, null=True, blank=True)
    chat = models.ForeignKey(ChatModel, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='Chat/Attachments', max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True , blank=True, null=True)


class MessageModel(models.Model):
    chat = models.ForeignKey(ChatModel, on_delete=models.CASCADE, blank=True, null=True, related_name = 'messages')
    sender = models.ForeignKey(UserModel, on_delete=models.CASCADE, null=True, blank=True)
    sent_at = models.DateTimeField(default=timezone.now)
    message = models.TextField(blank=True, null=True)
    reply_message = models.JSONField(null=True, blank=True)
    files_attachment = models.ForeignKey(ChatAttachmentModel, on_delete=models.CASCADE, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    # attachment_url = models.URLField(blank=True, null=True, max_length=500)
    # attachment_file_name = models.SlugField(blank=True, null=True, max_length=300)
    # is_read = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return str(self.chat)

    class Meta:
        ordering = ('sent_at',)
        verbose_name = 'message'
        verbose_name_plural = 'messages'


# class HelloModel(models.Model):
#     name = models.CharField(max_length=10)


