from django.urls import path
from .views import (
    FollowUserView,
    UnfollowUserView,
    FollowingListView,
    FollowersListView,
    NotificationListView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    UpdateFCMTokenView,
    HandleFollowRequestView,
    PendingFollowRequestsView
)

urlpatterns = [
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('following/', FollowingListView.as_view(), name='following-list'),
    path('followers/', FollowersListView.as_view(), name='followers-list'),
    # path('following/<int:id>/', FollowingListView.as_view(), name='following-list-by-id'),
    # path('followers/<int:id>/', FollowersListView.as_view(), name='followers-list-by-id'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/read-all/', MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    path('fcm-token/', UpdateFCMTokenView.as_view(), name='update-fcm-token'),
    path('follow-request/', HandleFollowRequestView.as_view(), name='handle-follow-request'),
    path('pending-requests/', PendingFollowRequestsView.as_view(), name='pending-follow-requests'),
] 