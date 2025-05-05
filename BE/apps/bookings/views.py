from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Equipment, Booking, QRCode, EquipmentType
from .serializers import BookingSerializer, EquipmentSerializer, EquipmentTypeSerializer
from .services import process_qr_scan, update_booking_status
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from django.core.files.base import ContentFile
from drf_spectacular.utils import extend_schema
class BookingListCreateAPIView(generics.ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        equipment_requests = serializer.validated_data.pop('equipment_requests', None)
        booking = Booking.create_booking(
            user_id=self.request.user.id,
            space_id=serializer.validated_data['space'].id,  # Sử dụng space_id từ validated_data
            start_time=serializer.validated_data['start_time'],
            end_time=serializer.validated_data['end_time'],
            equipment_requests=equipment_requests
        )
        serializer.instance = booking
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        booking_data = serializer.data
        user_email = request.user.email
        qr_code = serializer.instance.qr_code  # Lấy QRCode từ Booking vừa tạo
        if user_email and qr_code and qr_code.image:
            # Đọc hình ảnh mã QR
            image_file = qr_code.image
            with image_file.open('rb') as f:
                image_data = f.read()
            # Tạo nội dung HTML với ảnh nhúng
            cid = "qr_code_image"  # Content-ID cho ảnh
            html_content = (
                f"Chào bạn,<br><br>Đặt chỗ của bạn đã thành công!<br><br>"
                f'<img src="cid:{cid}" alt="QR Code"><br><br>'
                f"Trân trọng,<br>Hệ thống"
            )
            # Tạo email
            email = EmailMessage(
                'Đặt chỗ thành công',
                html_content,
                settings.EMAIL_HOST_USER,
                [user_email],
            )
            email.content_subtype = "html"  # Đặt nội dung là HTML
            email.attach('qr_code.png', image_data, 'image/png')  # Gắn ảnh
            email.send()
        return Response({
            'message': 'Đặt chỗ thành công',
            'data': booking_data
        }, status=201)
class EquipmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer


class EquipmentTypeListCreateAPIView(generics.ListCreateAPIView):
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer


@extend_schema(
    operation_id="scan_qr_code",
    summary="Quét mã QR để xác thực thông tin đặt chỗ",
    description="API nhận mã QR và dữ liệu liên quan để xác thực thông tin đặt chỗ. Nếu mã QR hợp lệ, thông tin đặt chỗ sẽ được trả về.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'qr_code_id': {'type': 'integer', 'example': 3},
                'qr_data': {'type': 'string', 'example': 'QR ID: 3\nBooking ID: 3\nUser: khiem\nSpace: Inv-01\nTime: 2025-05-05 14:08:00+00:00--2025-05-05 16:08:00+00:00'},
            },
            'required': ['qr_code_id', 'qr_data'],
        }
    },
    responses={
        200: BookingSerializer,
        400: {
            'type': 'object',
            'properties': {
                'error': {'type': 'string', 'example': 'ID mã QR không được cung cấp'}
            }
        }
    },
)
@api_view(['POST'])
def scan_qr_code(request):
    qr_code_id = request.data.get('qr_code_id')
    qr_data = request.data.get('qr_data')
    if not qr_code_id:
        return Response({'error': 'ID mã QR không được cung cấp'}, status=400)
    if not qr_data:
        return Response({'error': 'Dữ liệu QR không được cung cấp'}, status=400)
    try:
        booking = process_qr_scan(qr_code_id, qr_data)
        return Response(BookingSerializer(booking).data)
    except ValidationError as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
def update_booking_status_view(request):
    booking_id = request.data.get('booking_id')
    new_status = request.data.get('status')
    booking = update_booking_status(booking_id, new_status)
    return Response(BookingSerializer(booking).data)

