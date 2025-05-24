from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from .models import User, SuperUserProfile
from django.contrib.contenttypes.models import ContentType


@receiver(post_save, sender=User)
def create_superuser_profile(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        SuperUserProfile.objects.create(user=instance)


@receiver(post_migrate)
def setup_default_groups_and_permissions(sender, **kwargs):
    """
    Tạo các nhóm mặc định và gán quyền mặc định sau khi migration.
    Chỉ chạy cho ứng dụng 'users'.
    """
    if sender.name != 'users':
        return

    # Lấy content type cho model User
    try:
        user_content_type = ContentType.objects.get(app_label='apps.users', model='User')
    except ContentType.DoesNotExist:
        return

    # Danh sách quyền mặc định cho từng nhóm
    group_permissions = {
        'Students': [
            'view_own_profile',
            'edit_own_profile',
        ],
        'Teachers': [
            'view_own_profile',
            'edit_own_profile',
        ],
        'Managers': [
            'view_own_profile',
            'edit_own_profile',
            'view_all_users',
            'generate_report',
        ],
    }

    # Tạo nhóm và gán quyền
    for group_name, permission_codenames in group_permissions.items():
        group, created = Group.objects.get_or_create(name=group_name)
        # Gán quyền mặc định nếu nhóm mới tạo hoặc chưa có quyền
        if created or not group.permissions.exists():
            for codename in permission_codenames:
                try:
                    permission = Permission.objects.get(
                        content_type=user_content_type,
                        codename=codename
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"Permission {codename} not found for app 'users'.")
            group.save()