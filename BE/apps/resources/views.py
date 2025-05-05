from rest_framework import generics
from .models import StudySpace
from .serializers import StudySpaceSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from apps.bookings.models import Booking
from django.utils import timezone
from drf_spectacular.utils import extend_schema
# Create your views here.
class StudySpaceListCreateAPIView(generics.ListCreateAPIView):
    queryset = StudySpace.objects.all()
    serializer_class = StudySpaceSerializer

class StudySpaceRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = StudySpace.objects.all()
    serializer_class = StudySpaceSerializer


extend_schema(
    operation_id="get_space_status",
    summary="Lấy trạng thái của một không gian học tập",
    description="API này trả về trạng thái hiện tại của một không gian học tập dựa trên ID của không gian và thời gian cụ thể (nếu được cung cấp).",
    parameters=[
        {
            'name': 'space_id',
            'in': 'path',
            'required': True,
            'description': 'ID của không gian học tập',
            'schema': {'type': 'integer', 'example': 1},
        },
        {
            'name': 'at_time',
            'in': 'query',
            'required': False,
            'description': 'Thời gian cụ thể để kiểm tra trạng thái (ISO 8601 format)',
            'schema': {'type': 'string', 'format': 'date-time', 'example': '2025-05-05T14:00:00+07:00'},
        },
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'EMPTY'}
            }
        },
        404: {
            'type': 'object',
            'properties': {
                'error': {'type': 'string', 'example': 'Space not found'}
            }
        }
    },
)
@api_view(['GET'])
def get_space_status(request, space_id):
    try:
        space = StudySpace.objects.get(id=space_id)
        at_time = request.GET.get('at_time', timezone.now())
        status = space.get_space_status(at_time)
        return Response({'status': status})
    except StudySpace.DoesNotExist:
        return Response({'error': 'Space not found'}, status=404)

@extend_schema(
    operation_id="search_available_spaces",
    summary="Tìm kiếm không gian học tập trống",
    description="Tìm kiếm các không gian học tập trống dựa trên loại không gian và khung giờ.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'space_type': {'type': 'string', 'example': 'INDIVIDUAL'},
                'start_time': {'type': 'string', 'format': 'date-time', 'example': '2025-05-05T14:00:00+00:00'},
                'end_time': {'type': 'string', 'format': 'date-time', 'example': '2025-05-05T16:00:00+00:00'},
            },
            'required': ['space_type', 'start_time', 'end_time'],
        }
    },
    responses={
        200: StudySpaceSerializer(many=True),
        400: {
            'type': 'object',
            'properties': {
                'error': {'type': 'string', 'example': 'space_type không được cung cấp'}
            }
        }
    },
)
@api_view(['POST'])
def search_available_spaces(request):
    """Tìm kiếm không gian trống theo space_type và khung giờ"""
    space_type = request.data.get('space_type')
    start_time_str = request.data.get('start_time')
    end_time_str = request.data.get('end_time')

    # Kiểm tra dữ liệu đầu vào
    if not space_type:
        return Response({'error': 'space_type không được cung cấp'}, status=400)
    if not start_time_str:
        return Response({'error': 'start_time không được cung cấp'}, status=400)
    if not end_time_str:
        return Response({'error': 'end_time không được cung cấp'}, status=400)

    try:
        start_time = timezone.datetime.fromisoformat(start_time_str.replace(' ', 'T'))
        end_time = timezone.datetime.fromisoformat(end_time_str.replace(' ', 'T'))
    except ValueError:
        return Response({'error': 'Định dạng thời gian không hợp lệ (phải là ISO format)'}, status=400)

    if start_time >= end_time:
        return Response({'error': 'Thời gian bắt đầu phải trước thời gian kết thúc'}, status=400)

    # Lọc các StudySpace theo space_type
    spaces = StudySpace.objects.filter(space_type=space_type)
    available_spaces = []

    # Kiểm tra từng không gian xem có trống không
    for space in spaces:
        if Booking.check_room_availability(space, start_time, end_time):
            available_spaces.append(space)

    # Serialize kết quả
    serializer = StudySpaceSerializer(available_spaces, many=True)
    return Response(serializer.data)