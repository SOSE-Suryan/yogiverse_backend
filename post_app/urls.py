from django.urls import path, include
from rest_framework.routers import DefaultRouter
from post_app.View.PostViews import PostViewSet
from post_app.View.ReelViews import ReelViewSet
from post_app.View.StoryViews import StoryViewSet, StoryViewCreateAPIView, StoryViewersListAPIView
from post_app.View.CommentViews import CommentListAPIView, CommentCreateAPIView, CommentUpdateAPIView, CommentDeleteAPIView
from post_app.View.LikeToggleViews import LikeToggleAPIView, LikeListAPIView
from post_app.View.TrendingContentAPIViews import TrendingContentAPIView
from post_app.View.CollectionsViews import CollectionListCreateAPIView, CollectionDetailAPIView, AddToCollectionAPIView, RemoveFromCollectionAPIView, DeleteCollectionAPIView
from post_app.View.SearchExploreViews import SearchExploreAPIView
from post_app.View.RecentSearchViews import RecentSearchCreateAPIView, RecentSearchListAPIView, RecentSearchDeleteAPIView, ClearAllRecentSearchesAPIView
from post_app.View.RelatedContentViews import RelatedContentAPIView
from post_app.View.ShareContentViews import ShareContentAPIView
from post_app.View.HomePageViews import CombinedFeedAPIView
from post_app.View.HighlightsViews import HighlightViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'reels', ReelViewSet, basename='reels')
router.register(r'stories', StoryViewSet, basename='stories')
router.register(r'highlights', HighlightViewSet, basename='highlight')

urlpatterns = [
    path('', include(router.urls)),
    path('home-feed/', CombinedFeedAPIView.as_view(), name='home-feed'),
    path('like-toggle/', LikeToggleAPIView.as_view(), name='like-toggle'),
    path('like/list/', LikeListAPIView.as_view(), name='like-list'),
    path('comment/list/', CommentListAPIView.as_view(), name='comment-list'),
    path('comment/', CommentCreateAPIView.as_view(), name='comment-create'),
    path('comment/<int:pk>/edit/', CommentUpdateAPIView.as_view(), name='comment-edit'),
    path('comment/<int:pk>/delete/', CommentDeleteAPIView.as_view(), name='comment-delete'),
    path('trending/', TrendingContentAPIView.as_view(), name='trending-content'),
    path('collections/', CollectionListCreateAPIView.as_view(), name='collection-list-create'),
    path('collections/<int:pk>/', CollectionDetailAPIView.as_view(), name='collection-detail'),
    path('collections/items/', AddToCollectionAPIView.as_view(), name='add-to-collection'),
    path('collections/<int:collection_id>/<str:content_type>/<int:object_id>/', RemoveFromCollectionAPIView.as_view(), name='remove-from-collection'),
    path('collections/<int:pk>/delete/', DeleteCollectionAPIView.as_view(), name='delete-collection'),
    path('search/', SearchExploreAPIView.as_view(), name='search-explore'),
    path('search-history/', RecentSearchListAPIView.as_view(), name='search-history-list'),
    path('search-history/create/', RecentSearchCreateAPIView.as_view(), name='search-history-create'),
    path('search-history/<int:pk>/delete/', RecentSearchDeleteAPIView.as_view(), name='delete-single-search'),
    path('search-history/clear/', ClearAllRecentSearchesAPIView.as_view(), name='clear-all-search'),
    path('related-content/', RelatedContentAPIView.as_view(), name='related-content'),
    path('share/', ShareContentAPIView.as_view(), name='share-content'),

    path('stories/<int:story_id>/view/', StoryViewCreateAPIView.as_view(), name='story-view'),
    path('stories/<int:story_id>/viewers/', StoryViewersListAPIView.as_view(), name='story-viewers'),

]