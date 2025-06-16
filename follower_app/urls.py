from django.urls import path
from .views import (
    FollowUserView,
    UnfollowUserView,
    FollowingListView,
    FollowersListView,
    NotificationListView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    UpdateFCMTokenView
)

urlpatterns = [
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('following/', FollowingListView.as_view(), name='following-list'),
    path('followers/', FollowersListView.as_view(), name='followers-list'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/mark-read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/mark-all-read/', MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    path('update-fcm-token/', UpdateFCMTokenView.as_view(), name='update-fcm-token'),
] 