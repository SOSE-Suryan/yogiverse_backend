from django.db import models
from django.contrib.auth import get_user_model
from user_app.models import UserModel
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
import uuid
import string
import random


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
    is_like = models.BooleanField(default=False)

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
# Tag MODEL
# -------------------------

class Tag(TimeStampedModel):
    name = models.CharField(max_length=50, )
    slug = models.SlugField(max_length=60,blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


def generate_unique_slug(model_class):
    while True:
        slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        if not model_class.objects.filter(slug=slug).exists():
            return slug
        
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
    tags = models.ManyToManyField(Tag, related_name='tag_posts', blank=True)

    slug = models.SlugField(unique=True, blank=True)
    
    likes = GenericRelation(Like)
    comments = GenericRelation(Comment)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Post"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Post)
        super().save(*args, **kwargs)

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
    tags = models.ManyToManyField(Tag, related_name='tag_reels', blank=True)

    slug = models.SlugField(unique=True, blank=True)

    likes = GenericRelation(Like)
    comments = GenericRelation(Comment)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Reel"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Reel)
        super().save(*args, **kwargs)

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


# -------------------------
# Collection MODEL
# -------------------------
class Collection(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.name}"


class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='items')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    saved_at = models.DateTimeField(auto_now_add=True)
    is_collection = models.BooleanField(default=False)

    class Meta:
        unique_together = ('collection', 'content_type', 'object_id')  # Avoid duplicates in same collection


class RecentSearch(TimeStampedModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=255, blank=True, null=True)  # for text searches

    # Generic relation to Post, Reel, User, etc.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['user', 'searched_at']),
        ]

    def __str__(self):
        return f"{self.user.username} searched {self.query or self.content_object}"
