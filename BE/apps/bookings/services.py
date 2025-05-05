from rest_framework.exceptions import ValidationError
from .models import QRCode, Booking, Equipment, SPACE_STATUS_MAPPING
from django.utils import timezone
from datetime import timedelta
from dateutil.parser import parse
from django.utils.timezone import localtime

def validate_qr_data(qr_code_id, qr_data):
    """Xác thực dữ liệu QR dựa trên qr_code_id và qr_data"""
    try:
        qr_code = QRCode.objects.get(id=qr_code_id)
        qr_info = dict(item.split(": ") for item in qr_data.split("\n"))
        print(f"QR Info: {qr_info}")
        qr_id = int(qr_info.get('QR ID', '-1'))
        booking_id = int(qr_info.get('Booking ID', '-1'))
        if qr_id != qr_code.id or booking_id != qr_code.booking.id:
            print(f"ID mismatch: qr_id={qr_id}, qr_code.id={qr_code.id}, booking_id={booking_id}, booking.id={qr_code.booking.id}")
            return False
        current_time = localtime(timezone.now())  # Chuyển current_time sang múi giờ Việt Nam
        time_str = qr_info.get('Time', '')
        if not time_str:
            print("Time field missing")
            return False
        # Tách thành start và end dựa trên ký tự '-' cuối cùng
        time_parts = time_str.rsplit('--', 1)
        if len(time_parts) != 2:
            print(f"Invalid Time format: {time_str}")
            return False
        start_time_str = time_parts[0].strip()
        end_time_str = time_parts[1].strip()
        start_time = parse(start_time_str)
        end_time = parse(end_time_str)
        print(f"Time check: current={current_time}, start={start_time}, end={end_time}")
        if not (start_time <= current_time <= end_time):
            print(f"Time mismatch: current_time={current_time}, start_time={start_time}, end_time={end_time}")
            return False
        if qr_code.booking.status not in ['CONFIRMED', 'CHECK_IN']:
            print(f"Invalid status: {qr_code.booking.status}")
            return False
        print(f"QR Code {qr_code_id} validated successfully.")
        return True
    except QRCode.DoesNotExist:
        print(f"QRCode with id={qr_code_id} does not exist")
        return False
    except (KeyError, ValueError, IndexError) as e:
        print(f"Parse error: {str(e)}")
        return False

def process_qr_scan(qr_code_id, qr_data):
    """Xử lý quét mã QR để check-in hoặc check-out"""
    try:
        if not validate_qr_data(qr_code_id, qr_data):
            raise ValidationError("Dữ liệu QR không hợp lệ.")

        qr_code = QRCode.objects.get(id=qr_code_id)
        booking = qr_code.booking
        current_time = timezone.now()

        if booking.status == 'CONFIRMED':
            booking.status = 'CHECK_IN'
            booking.space.space_status = SPACE_STATUS_MAPPING['CHECK_IN']
            print(f"Booking status updated to CHECK_IN for booking ID: {booking.id}")
            booking.space.save()
            booking.save()
            return booking
        elif booking.status == 'CHECK_IN':
            booking.status = 'CHECK_OUT'
            booking.space.space_status = SPACE_STATUS_MAPPING['CHECK_OUT']
            booking.space.save()
            return_equipment(booking)
            booking.save()
            return booking
        else:
            raise ValidationError("Booking không ở trạng thái phù hợp để quét (phải là CONFIRMED hoặc CHECK_IN).")
    except QRCode.DoesNotExist:
        raise ValidationError("Mã QR không tồn tại.")

def return_equipment(booking):
    """Trả thiết bị về pool"""
    for equipment in booking.equipments.all():
        equipment.status = 'AVAILABLE'
        equipment.booking = None
        equipment.save()

def update_booking_status(booking_id, new_status):
    """Cập nhật trạng thái booking và xử lý thiết bị nếu cần"""
    try:
        booking = Booking.objects.get(id=booking_id)
        if new_status not in [choice[0] for choice in Booking.STATUS_CHOICES]:
            raise ValidationError("Trạng thái không hợp lệ.")
        booking.status = new_status
        booking.space.space_status = SPACE_STATUS_MAPPING.get(new_status, 'EMPTY')
        booking.space.save()
        booking.save()
        if new_status in ['CHECK_OUT', 'CANCELLED']:
            return_equipment(booking)
        return booking
    except Booking.DoesNotExist:
        raise ValidationError("Booking không tồn tại.")

def auto_update_booking_status():
    """Tự động cập nhật trạng thái booking nếu quá thời gian"""
    current_time = timezone.now()
    bookings = Booking.objects.filter(
        status__in=['CONFIRMED', 'CHECK_IN']
    )

    for booking in bookings:
        # Tự động hủy nếu sau start_time 30 phút mà chưa check-in
        if (booking.status == 'CONFIRMED' and
            current_time > booking.start_time + timedelta(minutes=30)):
            booking.status = 'CANCELLED'
            booking.space.space_status = SPACE_STATUS_MAPPING['CANCELLED']
            booking.space.save()
            return_equipment(booking)
            booking.save()

        # Tự động check-out nếu sau end_time 30 phút mà chưa check-out
        elif (booking.status == 'CHECK_IN' and
              current_time > booking.end_time + timedelta(minutes=30)):
            booking.status = 'CHECK_OUT'
            booking.space.space_status = SPACE_STATUS_MAPPING['CHECK_OUT']
            booking.space.save()
            return_equipment(booking)
            booking.save()