from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, TeacherProfile, ManagerProfile, SuperUserProfile, Student, Teacher, Manager , SuperUser

# Inline để hiển thị profile
class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user'

class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name_plural = 'Teacher Profile'
    fk_name = 'user'

class ManagerProfileInline(admin.StackedInline):
    model = ManagerProfile
    can_delete = False
    verbose_name_plural = 'Manager Profile'
    fk_name = 'user'

class SuperUserProfileInline(admin.StackedInline):
    model = SuperUserProfile
    can_delete = False
    verbose_name_plural = 'Superuser Profile'
    fk_name = 'user'

# Admin cho proxy model Student
@admin.register(Student)
class StudentAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_id', 'get_major', 'is_active', 'get_direct_permissions')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'user_id')
    list_filter = ('is_active', 'groups')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'first_name', 'last_name', 'user_id', 'phone_number', 'address')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Quản lý nhóm và quyền của người dùng. Gán quyền trực tiếp để áp dụng cho cá nhân.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'user_id'),
        }),
    )
    inlines = [StudentProfileInline]
    ordering = ('username',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='student', is_superuser=False)

    def get_major(self, obj):
        return obj.student_profile.major if hasattr(obj, 'student_profile') else '-'
    get_major.short_description = 'Major'

    def get_direct_permissions(self, obj):
        return ", ".join([perm.codename for perm in obj.user_permissions.all()])
    get_direct_permissions.short_description = 'Direct Permissions'

# Admin cho proxy model Teacher
@admin.register(Teacher)
class TeacherAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_id', 'get_department', 'is_active', 'get_direct_permissions')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'user_id')
    list_filter = ('is_active', 'groups')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'first_name', 'last_name', 'user_id', 'phone_number', 'address')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Quản lý nhóm và quyền của người dùng. Gán quyền trực tiếp để áp dụng cho cá nhân.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'user_id'),
        }),
    )
    inlines = [TeacherProfileInline]
    ordering = ('username',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='teacher', is_superuser=False)

    def get_department(self, obj):
        return obj.teacher_profile.department if hasattr(obj, 'teacher_profile') else '-'
    get_department.short_description = 'Department'

    def get_direct_permissions(self, obj):
        return ", ".join([perm.codename for perm in obj.user_permissions.all()])
    get_direct_permissions.short_description = 'Direct Permissions'

# Admin cho proxy model Manager
@admin.register(Manager)
class ManagerAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_id', 'get_role_description', 'is_active', 'get_direct_permissions')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'user_id')
    list_filter = ('is_active', 'groups')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'first_name', 'last_name', 'user_id', 'phone_number', 'address')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Quản lý nhóm và quyền của người dùng. Gán quyền trực tiếp để áp dụng cho cá nhân.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'user_id'),
        }),
    )
    inlines = [ManagerProfileInline]
    ordering = ('username',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='manager', is_superuser=False)

    def get_role_description(self, obj):
        return obj.manager_profile.role_description if hasattr(obj, 'manager_profile') else '-'
    get_role_description.short_description = 'Role Description'

    def get_direct_permissions(self, obj):
        return ", ".join([perm.codename for perm in obj.user_permissions.all()])
    get_direct_permissions.short_description = 'Direct Permissions'

# Admin cho proxy model SuperUser
@admin.register(SuperUser)
class SuperUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_staff_id', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'first_name', 'last_name', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    inlines = [SuperUserProfileInline]
    ordering = ('username',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_superuser=True)

    def get_staff_id(self, obj):
        return obj.superuser_profile.staff_id if hasattr(obj, 'superuser_profile') else '-'
    get_staff_id.short_description = 'Staff ID'