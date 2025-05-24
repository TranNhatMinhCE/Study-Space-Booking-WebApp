from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import User, StudentProfile, TeacherProfile, ManagerProfile, SuperUserProfile
from django.contrib import messages
from django import forms

# Hủy đăng ký Group mặc định để sử dụng GroupAdmin tùy chỉnh
admin.site.unregister(Group)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'user_id', 'is_staff', 'is_superuser', 'groups_display')
    list_filter = ('role', 'groups', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'user_id')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role', 'user_id', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    filter_horizontal = ('groups', 'user_permissions')  # Giao diện kéo-thả cho groups và permissions
    
    actions = ['assign_to_group', 'remove_from_group']  # Thêm hành động hàng loạt

    def groups_display(self, obj):
        """Hiển thị danh sách nhóm của user trong danh sách"""
        return ", ".join([group.name for group in obj.groups.all()])
    groups_display.short_description = 'Groups'

    def assign_to_group(self, request, queryset):
        group_id = request.POST.get('group_id')
        if not group_id:
            self.message_user(request, "Vui lòng chọn một nhóm để gán.", level=messages.ERROR)
            return
        try:
            group = Group.objects.get(id=group_id)
            for user in queryset:
                user.groups.add(group)
            self.message_user(request, f"Đã gán {queryset.count()} user vào nhóm {group.name}.", level=messages.SUCCESS)
        except Group.DoesNotExist:
            self.message_user(request, "Nhóm không tồn tại.", level=messages.ERROR)

    assign_to_group.short_description = "Gán user vào nhóm"

    def remove_from_group(self, request, queryset):
        group_id = request.POST.get('group_id')
        if not group_id:
            self.message_user(request, "Vui lòng chọn một nhóm để bỏ.", level=messages.ERROR)
            return
        try:
            group = Group.objects.get(id=group_id)
            for user in queryset:
                user.groups.remove(group)
            self.message_user(request, f"Đã bỏ {queryset.count()} user khỏi nhóm {group.name}.", level=messages.SUCCESS)
        except Group.DoesNotExist:
            self.message_user(request, "Nhóm không tồn tại.", level=messages.ERROR)

    remove_from_group.short_description = "Bỏ user khỏi nhóm"

    def get_form(self, request, obj=None, **kwargs):
        # print("Form fields:", form.base_fields)
        form = super().get_form(request, obj, **kwargs)
        if 'assign_to_group' in self.actions or 'remove_from_group' in self.actions:
            print("Adding group_id field to form") 
            form.base_fields['group_id'] = forms.ChoiceField(
                choices=[('', '---------')] + [(g.id, g.name) for g in Group.objects.all()],
                required=False,
                label="Chọn nhóm"
            )
        return form

@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    list_display = ('name', 'permission_count', 'user_count')
    list_filter = ('permissions__content_type__app_label',)  # Lọc theo ứng dụng
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Number of Permissions'

    def user_count(self, obj):
        return obj.user_set.count()
    user_count.short_description = 'Number of Users'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'content_type')
    list_filter = ('content_type__app_label',)
    search_fields = ('name', 'codename')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'major')
    search_fields = ('user__username', 'major')

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__username', 'department')

@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role_description')
    search_fields = ('user__username', 'role_description')

@admin.register(SuperUserProfile)
class SuperUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_id')
    search_fields = ('user__username', 'staff_id')