from rest_framework import serializers
from .models import Feedback, Notification, NotificationReadStatus, Comment
from apps.users.serializers import UserSerializer
from apps.users.models import User

class CommentSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'sender', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at']

class FeedbackSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    responded_by = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)  # Danh sách bình luận

    class Meta:
        model = Feedback
        fields = ['id', 'sender', 'content', 'status', 'response', 'responded_by', 'is_read', 'created_at', 'updated_at', 'comments']
        read_only_fields = ['id', 'sender', 'status', 'responded_by', 'created_at', 'updated_at']

class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['content']

class NotificationSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'sender', 'target_type', 'target_user', 'content', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']

    def get_is_read(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        read_status = obj.read_statuses.filter(user=user).first()
        return read_status.is_read if read_status else False

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['target_type', 'target_user', 'content']

    def validate(self, data):
        target_type = data.get('target_type')
        target_user = data.get('target_user')

        if target_type == 'specific_user' and not target_user:
            raise serializers.ValidationError("Target user is required for 'specific_user' target type.")
        if target_type != 'specific_user' and target_user:
            raise serializers.ValidationError("Target user should only be set for 'specific_user' target type.")
        return data

    def create(self, validated_data):
        notification = super().create(validated_data)
        target_type = validated_data.get('target_type')
        target_user = validated_data.get('target_user')

        if target_type == 'specific_user':
            NotificationReadStatus.objects.create(user=target_user, notification=notification)
        else:
            users = User.objects.filter(is_superuser=False)
            if target_type != 'all':
                users = users.filter(role=target_type)
            for user in users:
                NotificationReadStatus.objects.create(user=user, notification=notification)

        return notification