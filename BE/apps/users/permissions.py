from rest_framework import permissions


class HasViewOwnProfilePermission(permissions.BasePermission):
    """
    Kiểm tra quyền xem profile của chính người dùng.
    - Dựa trên permission 'view_own_profile'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('users.view_own_profile')

class HasEditOwnProfilePermission(permissions.BasePermission):
    """
    Kiểm tra quyền chỉnh sửa profile của chính người dùng.
    - Dựa trên permission 'edit_own_profile'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('users.edit_own_profile')

class HasViewAllUsersPermission(permissions.BasePermission):
    """
    Kiểm tra quyền xem danh sách tất cả người dùng.
    - Dựa trên permission 'view_all_users'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('users.view_all_users')

class HasGenerateReportPermission(permissions.BasePermission):
    """
    Kiểm tra quyền tạo báo cáo thống kê.
    - Dựa trên permission 'generate_report'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('users.generate_report')

class IsOwnProfile(permissions.BasePermission):
    """
    Kiểm tra ở cấp độ object (object-level).
    - Đảm bảo người dùng chỉ truy cập profile của chính họ.
    """
    def has_object_permission(self, request, view, obj):
        # obj là profile (StudentProfile, TeacherProfile, ManagerProfile)
        return obj.user == request.user
    

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'