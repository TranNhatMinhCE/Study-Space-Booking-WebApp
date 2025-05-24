from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Equipment, Booking, QRCode, EquipmentType
from apps.resources.models import StudySpace
from .serializers import BookingSerializer, EquipmentSerializer, EquipmentTypeSerializer
from .services import process_qr_scan, update_booking_status
from .permissions import IsStudentOrTeacher, IsManager, IsBookingOwner, CanCancelBooking
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class BookingListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsStudentOrTeacher | IsManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # Lấy tham số status từ query string
        status_filter = self.request.query_params.get('status', None)

        # Xác định queryset dựa trên vai trò người dùng
        if self.request.user.role == 'manager':
            queryset = Booking.objects.all()
        else:
            queryset = Booking.objects.filter(user=self.request.user)

        # Lọc theo trạng thái nếu có tham số status
        if status_filter:
            if status_filter not in [choice[0] for choice in Booking.STATUS_CHOICES]:
                raise ValidationError("Trạng thái không hợp lệ.")
            queryset = queryset.filter(status=status_filter)

        # Sắp xếp theo thời gian tạo
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        equipment_requests = serializer.validated_data.pop('equipment_requests', None)
        with transaction.atomic():
            space = StudySpace.objects.select_for_update().get(id=serializer.validated_data['space'].id)
            booking = Booking.create_booking(
                user_id=self.request.user.id,
                space_id=space.id,
                start_time=serializer.validated_data['start_time'],
                end_time=serializer.validated_data['end_time'],
                equipment_requests=equipment_requests
            )
            serializer.instance = booking

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
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
        }, status=status.HTTP_201_CREATED)

class EquipmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsManager]

class EquipmentTypeListCreateAPIView(generics.ListCreateAPIView):
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer
    permission_classes = [IsManager]

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
        qr_code = QRCode.objects.get(id=qr_code_id)
        # Kiểm tra quyền
        if request.user.role != 'manager' and qr_code.booking.user != request.user:
            return Response({'error': 'Bạn không có quyền thực hiện hành động này'}, status=403)

        with transaction.atomic():
            space = StudySpace.objects.select_for_update().get(id=qr_code.booking.space.id)
            booking = process_qr_scan(qr_code_id, qr_data)
            return Response(BookingSerializer(booking, context={'request': request}).data)
    except ValidationError as e:
        return Response({'error': str(e)}, status=400)
    except QRCode.DoesNotExist:
        return Response({'error': 'Mã QR không tồn tại'}, status=404)

@api_view(['POST'])
def update_booking_status_view(request):
    booking_id = request.data.get('booking_id')
    new_status = request.data.get('status')

    try:
        booking = Booking.objects.get(id=booking_id)
        # Kiểm tra quyền
        if request.user.role != 'manager' and booking.user != request.user:
            return Response({'error': 'Bạn không có quyền thực hiện hành động này'}, status=403)

        with transaction.atomic():
            space = StudySpace.objects.select_for_update().get(id=booking.space.id)
            booking = update_booking_status(booking_id, new_status)
            return Response(BookingSerializer(booking, context={'request': request}).data)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking không tồn tại'}, status=404)
    except ValidationError as e:
        return Response({'error': str(e)}, status=400)

@extend_schema(
    operation_id="cancel_booking",
    summary="Hủy đặt phòng",
    description="API này cho phép người dùng hủy một đặt phòng. Chỉ người quản lý hoặc người dùng sở hữu đặt phòng ở trạng thái 'CONFIRMED' mới có quyền hủy.",
    parameters=[
        {
            'name': 'booking_id',
            'in': 'path',
            'required': True,
            'description': 'ID của đặt phòng cần hủy',
            'schema': {'type': 'integer', 'example': 1},
        }
    ],
    responses={
        200: BookingSerializer,
        403: {
            'type': 'object',
            'properties': {
                'error': {'type': 'string', 'example': 'Bạn không có quyền hủy đặt phòng này'},
            },
        },
        404: {
            'type': 'object',
            'properties': {
                'error': {'type': 'string', 'example': 'Booking không tồn tại'},
            },
        },
        400: {
            'type': 'object',
            'properties': {
                'error': {'type': 'string', 'example': 'Trạng thái không hợp lệ'},
            },
        },
    },
) 
@api_view(['POST'])
def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        # Kiểm tra quyền
        if request.user.role != 'manager' and (booking.user != request.user or booking.status != 'CONFIRMED'):
            return Response({'error': 'Bạn không có quyền hủy đặt phòng này'}, status=403)

        with transaction.atomic():
            space = StudySpace.objects.select_for_update().get(id=booking.space.id)
            booking = update_booking_status(booking_id, 'CANCELLED')
            return Response(BookingSerializer(booking, context={'request': request}).data)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking không tồn tại'}, status=404)
    except ValidationError as e:
        return Response({'error': str(e)}, status=400)