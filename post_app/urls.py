from django.urls import path, include
from rest_framework.routers import DefaultRouter
from post_app.View.PostViews import PostViewSet
from post_app.View.ReelViews import ReelViewSet
from post_app.View.StoryViews import StoryViewSet
from post_app.View.CommentViews import CommentCreateAPIView, CommentUpdateAPIView, CommentDeleteAPIView
from post_app.View.LikeToggleViews import LikeToggleAPIView

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'reels', ReelViewSet, basename='reels')
router.register(r'stories', StoryViewSet, basename='stories')

urlpatterns = [
    path('', include(router.urls)),
    path('like-toggle/', LikeToggleAPIView.as_view(), name='like-toggle'),
    path('comment/', CommentCreateAPIView.as_view(), name='comment-create'),
    path('comment/<int:pk>/edit/', CommentUpdateAPIView.as_view(), name='comment-edit'),
    path('comment/<int:pk>/delete/', CommentDeleteAPIView.as_view(), name='comment-delete'),

]