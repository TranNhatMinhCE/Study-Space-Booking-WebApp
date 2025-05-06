from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        """
        Được gọi khi ứng dụng khởi động.
        - Import signals để đăng ký signal xử lý gán quyền.
        """
        import apps.users.signals