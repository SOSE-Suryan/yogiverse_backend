from django.contrib import admin
from .models import (
    Like,
    Comment,
    Tag,
    Post,
    PostMedia,
    Reel,
    Story,
    Collection,
    CollectionItem,
    RecentSearch,
)
from import_export.admin import ImportExportModelAdmin
# # Register your models here.

@admin.register(Post)
class PostModelAdmin(ImportExportModelAdmin):
    list_display = ("user","caption","is_draft","allow_comments","hide_like_count","location","tags","slug","likes","comments")
    search_fields = ("caption","location","slug","user__username","user__first_name","user__last_name","user__email")
    
    def tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    def likes(self, obj):
        return obj.likes.count()

    def comments(self, obj):
        return obj.comments.count()
    
@admin.register(Like)
class LikeAdmin(ImportExportModelAdmin):
    list_display = ("user", "content_type", "object_id", "is_like", "created_at")
    search_fields = ("user__username",)

@admin.register(Comment)
class CommentAdmin(ImportExportModelAdmin):
    list_display = ("user", "content_type", "object_id", "text", "created_at")
    search_fields = ("user__username", "text")

@admin.register(Tag)
class TagAdmin(ImportExportModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")

@admin.register(PostMedia)
class PostMediaAdmin(ImportExportModelAdmin):
    list_display = ("post", "media_file", "is_video")
    search_fields = ("post__caption",)

@admin.register(Reel)
class ReelAdmin(ImportExportModelAdmin):
    list_display = ("user", "caption", "video_file", "duration", "is_draft", "allow_comments", "hide_like_count", "music_track", "slug")
    search_fields = ("user__username", "caption", "music_track")

@admin.register(Story)
class StoryAdmin(ImportExportModelAdmin):
    list_display = ("user", "media_file", "caption", "expires_at", "is_highlighted")
    search_fields = ("user__username", "caption")

@admin.register(Collection)
class CollectionAdmin(ImportExportModelAdmin):
    list_display = ("user", "name", "created_at")
    search_fields = ("user__username", "name")

@admin.register(CollectionItem)
class CollectionItemAdmin(ImportExportModelAdmin):
    list_display = ("collection", "content_type", "object_id", "saved_at", "is_collection")
    search_fields = ("collection__name",)

@admin.register(RecentSearch)
class RecentSearchAdmin(ImportExportModelAdmin):
    list_display = ("user", "query", "content_type", "object_id", "searched_at")
    search_fields = ("user__username", "query")
