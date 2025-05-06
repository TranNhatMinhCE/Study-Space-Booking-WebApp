from django.contrib import admin
from .models import Feedback, Notification, NotificationReadStatus, Comment

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('sender', 'content', 'status', 'responded_by', 'is_read', 'created_at')
    search_fields = ('sender__username', 'content', 'response')
    list_filter = ('status', 'sender__role', 'is_read')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'manager':
            return qs
        return qs.none()

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('sender', 'feedback', 'content', 'created_at')
    search_fields = ('sender__username', 'content')
    list_filter = ('sender__role',)
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'manager':
            return qs
        return qs.filter(sender=request.user)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('sender', 'target_type', 'target_user', 'content', 'created_at')
    search_fields = ('sender__username', 'content')
    list_filter = ('target_type',)
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'manager':
            return qs
        return qs.none()

@admin.register(NotificationReadStatus)
class NotificationReadStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification', 'is_read')
    search_fields = ('user__username', 'notification__content')
    list_filter = ('is_read',)