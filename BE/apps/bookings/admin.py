from django.contrib import admin
from .models import Booking, Equipment, EquipmentType, QRCode, NotificationConfig

admin.site.register(Booking)
admin.site.register(EquipmentType)  
admin.site.register(Equipment)
admin.site.register(QRCode)

@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    list_display = ('reminder_before_checkin_minutes', 'reminder_before_checkout_minutes')
    fieldsets = (
        (None, {
            'fields': ('reminder_before_checkin_minutes', 'reminder_before_checkout_minutes')
        }),
    )

    def has_add_permission(self, request):
        # Chỉ cho phép một bản ghi duy nhất
        return not NotificationConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Không cho phép xóa
        return False