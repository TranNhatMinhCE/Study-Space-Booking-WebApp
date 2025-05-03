from django.db import models
from users.models import User
from resources.models import StudySpace
import qrcode
from django.core.files.base import ContentFile
import io
from PIL import Image
# Create your models here.
# Class Booking, BookingStatus, QRCode, Equipment, Schedule 
class BookingStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name

class EquipmentType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    total_quantity = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.name
    
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    space = models.ForeignKey(StudySpace, on_delete=models.CASCADE)
    status = models.ForeignKey(BookingStatus, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - {self.equipment_type.name} - {self.booking_date}"
    

class Equipment(models.Model):
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.PROTECT)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='equipments')
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Hoạt động'), ('broken', 'Hỏng'), ('maintenance', 'Bảo trì')],
        default='active'
    )
    def __str__(self):
       return f"{self.equipment_type.name} for Booking {self.booking.id}"
    
class QRCode(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='qr_code')
    image = models.ImageField(upload_to='qrcodes/')
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_qr_code(booking):
        # Logic to generate QR code image
        qr_code = QRCode.objects.create(booking=booking)
        qr_data = f"Booking ID: {qr_code.booking.id} \
                    \nUser: {qr_code.booking.user} \
                    \nSpace: {qr_code.booking.space} \
                    \nTime: {qr_code.booking.start_time}-{qr_code.booking.end_time}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code.image.save(f"qr_code_{qr_code.booking.id}.png", ContentFile(buffer.getvalue()), save=False)
        buffer.close()
        qr_code.save()
        return qr_code
    
    def __str__(self):
        return f"QR Code for Booking {self.booking.id}"