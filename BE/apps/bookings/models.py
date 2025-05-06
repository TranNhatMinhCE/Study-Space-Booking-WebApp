from django.db import models
from apps.users.models import User
# from django.contrib.auth.models import User
from apps.resources.models import StudySpace
import qrcode
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError
import io
from PIL import Image
from django.utils import timezone

# Ánh xạ giữa Booking.status và StudySpace.space_status
SPACE_STATUS_MAPPING = {
    'CONFIRMED': 'BOOKED',
    'CHECK_IN': 'INUSE',
    'CHECK_OUT': 'EMPTY',
    'CANCELLED': 'EMPTY',
}

class EquipmentType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    total_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
class Booking(models.Model):
    STATUS_CHOICES = (
        ('CONFIRMED', 'Đã xác nhận'), 
        ('CHECK_IN', 'Đã check in'), 
        ('CHECK_OUT', 'Đã check out'), 
        ('CANCELLED', 'Đã hủy'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    space = models.ForeignKey(StudySpace, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CONFIRMED'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.space.name}"

    @staticmethod
    def check_room_availability(studySpace, start_time, end_time):
        """Kiểm tra phòng có trống trong khoảng thời gian"""
        if studySpace.space_status == 'INUSE':
            return False
        return not Booking.objects.filter(
            space=studySpace,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(status='CANCELLED').exists()
    
    @staticmethod
    def check_equipment_availability(equipment_type_id, count, start_time, end_time):
        """Kiểm tra số lượng thiết bị khả dụng"""
        equipment_type = EquipmentType.objects.get(id=equipment_type_id)
        total_available = equipment_type.total_quantity - Equipment.objects.filter(
            equipment_type=equipment_type,
            status='BORROWED',
            booking__start_time__lt=end_time,
            booking__end_time__gt=start_time
        ).count()
        return total_available >= count
    
    @staticmethod
    def create_booking(user_id, space_id, start_time, end_time, equipment_requests=None):
        """Tạo một booking mới"""
        if start_time >= end_time:
            raise ValidationError("Thời gian bắt đầu phải trước thời gian kết thúc.")
        space = StudySpace.objects.get(id=space_id)
        if not Booking.check_room_availability(space, start_time, end_time):
            raise ValidationError("Phòng đã được đặt trong khoảng thời gian này.")
        user = User.objects.get(id=user_id)
        booking = Booking.objects.create(
            user=user,
            space=space,
            start_time=start_time,
            end_time=end_time
        )
        # Cập nhật space_status khi tạo booking
        space.space_status = SPACE_STATUS_MAPPING['CONFIRMED']
        space.save()
        if equipment_requests:
            for request in equipment_requests:
                equipment_type_id = request['equipment_type_id']
                count = request['count']
                if not Booking.check_equipment_availability(equipment_type_id, count, start_time, end_time):
                    raise ValidationError(f"Không đủ thiết bị {equipment_type_id} trong khoảng thời gian này.")
                available_equipments = Equipment.objects.filter(
                    equipment_type_id=equipment_type_id,
                    status='AVAILABLE',
                ).order_by('id')[:count]
                if len(available_equipments) < count:
                    booking.delete()
                    space.space_status = 'EMPTY'  # Rollback nếu không đủ thiết bị
                    space.save()
                    raise ValidationError(f"Không đủ thiết bị {equipment_type_id} khả dụng.")
                for equipment in available_equipments:
                    equipment.status = 'BORROWED'
                    equipment.booking = booking
                    equipment.save()
        QRCode.generate_qr_code(booking)
        return booking

class Equipment(models.Model):
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.PROTECT)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipments')
    status = models.CharField(
        max_length=20,
        choices=[('AVAILABLE', 'Available'),
                 ('BORROWED', 'Borrowed'),
                 ('BROKEN', 'broken'),
                 ('MAINTENANCE', 'maintenance')],
        default='AVAILABLE'
    )

    def __str__(self):
        booking_id = self.booking.id if self.booking else "None"
        return f"{self.equipment_type.name} (ID: {self.id}) for Booking {booking_id}"

class QRCode(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='qr_code')
    image = models.ImageField(upload_to='qrcodes/')
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_qr_code(booking):
        # Logic to generate QR code image
        qr_code = QRCode.objects.create(booking=booking)
        qr_data = f"QR ID: {qr_code.id} \
                    \nBooking ID: {qr_code.booking.id} \
                    \nUser: {qr_code.booking.user} \
                    \nSpace: {qr_code.booking.space} \
                    \nTime: {qr_code.booking.start_time}--{qr_code.booking.end_time}"
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

    def validate_qr_code(self):
        """Kiểm tra tính hợp lệ của mã QR dựa trên Booking.status"""
        current_time = timezone.now()
        if not (self.booking.start_time <= current_time <= self.booking.end_time):
            return False
        if self.booking.status != 'CONFIRMED':
            return False
        return True
    
    def __str__(self):
        return f"QR Code for Booking {self.booking.id}"


class NotificationConfig(models.Model):
    reminder_before_checkin_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Số phút trước giờ check-in để gửi thông báo (mặc định: 15 phút)."
    )
    reminder_before_checkout_minutes = models.PositiveIntegerField(
        default=10,
        help_text="Số phút trước giờ kết thúc để gửi thông báo (mặc định: 10 phút)."
    )

    class Meta:
        verbose_name = "Cấu hình thông báo"
        verbose_name_plural = "Cấu hình thông báo"

    def __str__(self):
        return f"Thông báo: {self.reminder_before_checkin_minutes} phút trước check-in, {self.reminder_before_checkout_minutes} phút trước check-out"

    @classmethod
    def get_config(cls):
        # Luôn lấy bản ghi đầu tiên, nếu không tồn tại thì tạo mới
        config, created = cls.objects.get_or_create(pk=1)
        return config