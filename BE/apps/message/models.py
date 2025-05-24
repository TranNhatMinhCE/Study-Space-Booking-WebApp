from django.db import models
from apps.users.models import User

class Feedback(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Đang chờ xử lý'),
        ('responded', 'Đã trả lời'),
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_feedbacks',
        limit_choices_to={'role__in': ['student', 'teacher']},
    )
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='responded_feedbacks',
        limit_choices_to={'role': 'manager'},
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.sender.username} - {self.status}"

class Comment(models.Model):
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_comments',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']  # Sắp xếp bình luận theo thời gian tạo

    def __str__(self):
        return f"Comment by {self.sender.username} on Feedback {self.feedback.id}"

class Notification(models.Model):
    TARGET_CHOICES = (
        ('all', 'Tất cả người dùng'),
        ('student', 'Sinh viên'),
        ('teacher', 'Giảng viên'),
        ('manager', 'Ban quản lý'),
        ('specific_user', 'Người dùng cụ thể'),
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        limit_choices_to={'role': 'manager'},
    )
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_notifications',
        null=True,
        blank=True,
        help_text="Chỉ điền nếu target_type là 'specific_user'."
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification from {self.sender.username} to {self.target_type}"

class NotificationReadStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_read_statuses')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='read_statuses')
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'notification')

    def __str__(self):
        return f"{self.user.username} - {self.notification.content} - {'Read' if self.is_read else 'Unread'}"