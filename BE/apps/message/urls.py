from django.urls import path
from .views import (
    FeedbackCreateView, FeedbackListView, FeedbackRespondView, FeedbackMarkReadView,
    CommentCreateView,
    NotificationCreateView, NotificationListView, NotificationMarkReadView, NewFeedbackNotificationCountView
)

urlpatterns = [
    path('feedbacks/', FeedbackCreateView.as_view(), name='feedback-create'),
    path('feedbacks/list/', FeedbackListView.as_view(), name='feedback-list'),
    path('feedbacks/<int:pk>/respond/', FeedbackRespondView.as_view(), name='feedback-respond'),
    path('feedbacks/<int:pk>/mark-read/', FeedbackMarkReadView.as_view(), name='feedback-mark-read'),
    path('feedbacks/<int:pk>/comments/', CommentCreateView.as_view(), name='comment-create'),
    
    path('notifications/', NotificationCreateView.as_view(), name='notification-create'),
    path('notifications/list/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('new-count/', NewFeedbackNotificationCountView.as_view(), name='new-feedback-notification-count'),
]