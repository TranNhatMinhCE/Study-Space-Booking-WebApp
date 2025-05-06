from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from .models import User, SuperUserProfile


@receiver(post_save, sender=User)
def assign_permissions_to_group(sender, instance, created, **kwargs):
    """
    Signal này được gọi sau khi một đối tượng User được tạo.
    - Kiểm tra role của user và gán quyền cho nhóm tương ứng.
    - Chỉ chạy khi user được tạo (created=True), không chạy khi cập nhật.
    """
    if created:  # Chỉ chạy khi user vừa được tạo
        # Lấy hoặc tạo nhóm dựa trên role
        group, _ = Group.objects.get_or_create(name=f"{instance.role.capitalize()}s")

        # Lấy các permission
        try:
            view_own_profile = Permission.objects.get(codename='view_own_profile')
            edit_own_profile = Permission.objects.get(codename='edit_own_profile')
            view_all_users = Permission.objects.get(codename='view_all_users')
            generate_report = Permission.objects.get(codename='generate_report')
        except Permission.DoesNotExist:
            # Nếu permission chưa tồn tại (do migration chưa chạy), bỏ qua
            return

        # Gán quyền cho nhóm dựa trên role
        if instance.role == 'student':
            group.permissions.add(view_own_profile, edit_own_profile)
        elif instance.role == 'teacher':
            group.permissions.add(view_own_profile, edit_own_profile)
        elif instance.role == 'manager':
            group.permissions.add(view_own_profile, edit_own_profile, view_all_users, generate_report)

        # Gán user vào nhóm (đã được thực hiện trong phương thức save, nhưng đảm bảo lại)
        instance.groups.add(group)

@receiver(post_save, sender=User)
def create_superuser_profile(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        SuperUserProfile.objects.create(user=instance)