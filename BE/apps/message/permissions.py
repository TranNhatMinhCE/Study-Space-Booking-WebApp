from rest_framework import permissions
from apps.users.models import User

class IsStudentOrTeacher(permissions.BasePermission):
    """
    Chỉ sinh viên và giảng viên có thể gửi phản hồi.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['student', 'teacher']

class IsManager(permissions.BasePermission):
    """
    Chỉ ban quản lý có thể xem và trả lời phản hồi.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'

class IsSenderOrManager(permissions.BasePermission):
    """
    Chỉ người gửi hoặc ban quản lý có thể xem phản hồi.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role in ['student', 'teacher', 'manager'])

    def has_object_permission(self, request, view, obj):
        # Ban quản lý có thể xem tất cả phản hồi
        if request.user.role == 'manager':
            return True
        # Người gửi chỉ xem được phản hồi của chính họ
        return obj.sender == request.user
    
class IsManagerForNotification(permissions.BasePermission):
    """
    Chỉ ban quản lý có thể gửi thông báo.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'

class CanCommentOnFeedback(permissions.BasePermission):
    """
    Chỉ người gửi phản hồi hoặc ban quản lý có thể bình luận.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role in ['student', 'teacher', 'manager'])

    def has_object_permission(self, request, view, obj):
        # obj là Feedback
        if request.user.role == 'manager':
            return True
        return obj.sender == request.user