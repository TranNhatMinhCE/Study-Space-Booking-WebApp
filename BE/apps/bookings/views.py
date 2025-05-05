from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Equipment, Booking, QRCode, EquipmentType
from .serializers import BookingSerializer, EquipmentSerializer, EquipmentTypeSerializer
from .services import process_qr_scan, update_booking_status
from django.utils import timezone
from django.core.exceptions import ValidationError

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

class EquipmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer


class EquipmentTypeListCreateAPIView(generics.ListCreateAPIView):
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer
    
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

