from django.contrib import admin
from .models import Booking, EquipmentType, Equipment, QRCode
# Register your models here.

admin.site.register(Booking)
admin.site.register(EquipmentType)  
admin.site.register(Equipment)
admin.site.register(QRCode)