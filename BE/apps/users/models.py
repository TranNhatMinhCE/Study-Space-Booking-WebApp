from django.contrib.auth.models import AbstractUser, Group
from django.db import models

class User(AbstractUser):
    """
    Model User đại diện cho tất cả người dùng trong hệ thống.
    - Kế thừa từ AbstractUser để sử dụng hệ thống xác thực mặc định của Django.
    - Sử dụng một bảng duy nhất với trường role để phân biệt loại người dùng.
    """
    ROLE_CHOICES = (
        ('student', 'Sinh viên'),
        ('teacher', 'Giảng viên'),
        ('manager', 'Ban quản lý'),
    )

    # full_name = models.CharField(max_length=100, blank=True, null=True)  # Tên đầy đủ của người dùng
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')  # Vai trò của người dùng
    user_id = models.CharField(max_length=20, blank=True, null=True, unique=True)  # Mã định danh chung (thay cho student_id và staff_id)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Số điện thoại
    address = models.TextField(blank=True, null=True)  # Địa chỉ
    created_at = models.DateTimeField(auto_now_add=True)  # Thời gian tạo
    updated_at = models.DateTimeField(auto_now=True)  # Thời gian cập nhật

    class Meta:
        # Định nghĩa các quyền tùy chỉnh
        permissions = [
            ('view_own_profile', 'Can view own profile'),
            ('edit_own_profile', 'Can edit own profile'),
            ('view_all_users', 'Can view all users'),
            ('generate_report', 'Can generate user report'),
        ]

    # def save(self, *args, **kwargs):
    #     """
    #     Ghi đè phương thức save để tự động gán user vào Group tương ứng với role.
    #     Ví dụ: role='student' -> gán vào group 'Students'.
    #     """
    #     if not self.pk or not self.groups.exists():
    #         super().save(*args, **kwargs)
    #         group, _ = Group.objects.get_or_create(name=self.role.capitalize() + 's')
    #         self.groups.add(group)
    #     else:
    #         super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class StudentProfile(models.Model):
    """
    Model lưu thông tin bổ sung cho sinh viên.
    - Liên kết 1-1 với User.
    - Chỉ được tạo nếu role='student'.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    major = models.CharField(max_length=100, blank=True, null=True)  # Ngành học

    def __str__(self):
        return f"Profile of {self.user.username}"

class TeacherProfile(models.Model):
    """
    Model lưu thông tin bổ sung cho giảng viên.
    - Liên kết 1-1 với User.
    - Chỉ được tạo nếu role='teacher'.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.CharField(max_length=100, blank=True, null=True)  # Khoa/Bộ môn

    def __str__(self):
        return f"Profile of {self.user.username}"

class ManagerProfile(models.Model):
    """
    Model lưu thông tin bổ sung cho ban quản lý.
    - Liên kết 1-1 với User.
    - Chỉ được tạo nếu role='manager'.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='manager_profile')
    role_description = models.TextField(blank=True, null=True)  # Mô tả vai trò

    def __str__(self):
        return f"Profile of {self.user.username}"

class SuperUserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='superuser_profile')
    staff_id = models.CharField(max_length=20, blank=True, null=True, unique=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

# Proxy models để tách biệt danh sách user trong admin
class Student(User):
    class Meta:
        proxy = True
        verbose_name = "Sinh viên"
        verbose_name_plural = "Sinh viên"

class Teacher(User):
    class Meta:
        proxy = True
        verbose_name = "Giảng viên"
        verbose_name_plural = "Giảng viên"

class Manager(User):
    class Meta:
        proxy = True
        verbose_name = "Ban quản lý"
        verbose_name_plural = "Ban quản lý"

class SuperUser(User):
    class Meta:
        proxy = True
        verbose_name = "Admins"
        verbose_name_plural = "Admins"