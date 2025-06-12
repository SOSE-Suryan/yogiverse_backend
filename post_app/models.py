from django.db import models
from django.contrib.auth import get_user_model
from user_app.models import UserModel
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# Common helper model
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# -------------------------
# Like MODEL
# -------------------------

class Like(TimeStampedModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='likes')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} liked {self.content_type} {self.object_id}"


# -------------------------
# Comment MODEL
# -------------------------

class Comment(TimeStampedModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='comments')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    text = models.TextField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} commented on {self.content_type} {self.object_id}"
    

# -------------------------
# POST MODEL
# -------------------------
class Post(TimeStampedModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='posts')
    caption = models.TextField(blank=True)
    is_draft = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    hide_like_count = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True)
    
    likes = GenericRelation(Like)
    comments = GenericRelation(Comment)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Post"

class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    media_file = models.FileField(upload_to='posts/')
    is_video = models.BooleanField(default=False)  # Use to differentiate image/video

# -------------------------
# REEL MODEL
# -------------------------
class Reel(TimeStampedModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='reels')
    caption = models.TextField(blank=True)
    video_file = models.FileField(upload_to='reels/')
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    is_draft = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    hide_like_count = models.BooleanField(default=False)
    music_track = models.CharField(max_length=255, blank=True)

    likes = GenericRelation(Like)
    comments = GenericRelation(Comment)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Reel"

# -------------------------
# STORY MODEL
# -------------------------
class Story(TimeStampedModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='stories')
    media_file = models.FileField(upload_to='stories/')
    caption = models.CharField(max_length=2200, blank=True)
    expires_at = models.DateTimeField()
    is_highlighted = models.BooleanField(default=False)  # For future Highlights feature

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Story"


