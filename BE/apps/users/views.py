from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserSerializer, StudentProfileSerializer, TeacherProfileSerializer, ManagerProfileSerializer
from .permissions import HasViewOwnProfilePermission, HasEditOwnProfilePermission, HasViewAllUsersPermission, HasGenerateReportPermission, IsOwnProfile
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import datetime, timedelta
from apps.resources.models import StudySpace
from apps.bookings.models import Booking, Equipment

# Class UserAPIView
class UserAPIView(APIView):
    """
    Class cha xử lý các chức năng chung của người dùng.
    - Đăng ký, đăng nhập, đăng xuất.
    - Không yêu cầu đăng nhập (AllowAny), trừ đăng xuất (IsAuthenticated).
    """
    permission_classes = [AllowAny]

    def post(self, request, action=None):
        if action == "register":
            """
            Xử lý đăng ký người dùng.
            - Sử dụng RegisterSerializer để tạo user và profile.
            """
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == "login":
            """
            Xử lý đăng nhập.
            - Xác thực username và password, trả về access token và refresh token.
            """
            username = request.data.get('username')
            password = request.data.get('password')
            if not username or not password:
                return Response(
                    {'error': 'Username and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user = authenticate(request=request, username=username, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data,
                })
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        elif action == "logout":
            """
            Xử lý đăng xuất.
            - Yêu cầu người dùng đã đăng nhập (IsAuthenticated).
            - Vô hiệu hóa refresh token.
            """
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            try:
                refresh_token = request.data.get("refresh")
                if not refresh_token:
                    return Response(
                        {'error': 'Refresh token is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response(status=status.HTTP_205_RESET_CONTENT)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

# Class StudentAPIView
class StudentAPIView(UserAPIView):
    """
    Class xử lý các chức năng của sinh viên.
    - Kế thừa từ UserAPIView để tái sử dụng các chức năng chung.
    - Yêu cầu người dùng đã đăng nhập và có quyền xem/chỉnh sửa profile.
    """
    permission_classes = [IsAuthenticated, HasViewOwnProfilePermission, HasEditOwnProfilePermission]

    def get(self, request, action=None):
        if action == "profile":
            """
            Xem profile của sinh viên.
            - Trả về thông tin profile của người dùng hiện tại.
            """
            serializer = StudentProfileSerializer(request.user.student_profile)
            return Response(serializer.data)

    def put(self, request, action=None):
        if action == "profile":
            """
            Cập nhật profile của sinh viên.
            - Chỉ cho phép cập nhật profile của chính người dùng.
            """
            serializer = StudentProfileSerializer(
                request.user.student_profile,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Class TeacherAPIView
class TeacherAPIView(UserAPIView):
    """
    Class xử lý các chức năng của giảng viên.
    - Tương tự StudentAPIView, nhưng dành cho giảng viên.
    """
    permission_classes = [IsAuthenticated, HasViewOwnProfilePermission, HasEditOwnProfilePermission]

    def get(self, request, action=None):
        if action == "profile":
            """
            Xem profile của giảng viên.
            """
            serializer = TeacherProfileSerializer(request.user.teacher_profile)
            return Response(serializer.data)

    def put(self, request, action=None):
        if action == "profile":
            """
            Cập nhật profile của giảng viên.
            """
            serializer = TeacherProfileSerializer(
                request.user.teacher_profile,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Class ManagerAPIView
class ManagerAPIView(UserAPIView):
    """
    Class xử lý các chức năng của ban quản lý.
    - Hỗ trợ xem danh sách người dùng và tạo báo cáo thống kê.
    """
    permission_classes = [IsAuthenticated, HasViewOwnProfilePermission, HasEditOwnProfilePermission]

    def get(self, request, action=None):
        if action == "profile":
            """
            Xem profile của ban quản lý.
            """
            serializer = ManagerProfileSerializer(request.user.manager_profile)
            return Response(serializer.data)

        elif action == "list-users":
            """
            Xem danh sách tất cả người dùng.
            - Yêu cầu quyền view_all_users.
            """
            if not request.user.has_perm('users.view_all_users'):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)

        elif action == "report":
            """
            Tạo báo cáo thống kê về người dùng.
            - Yêu cầu quyền generate_report.
            """
            if not request.user.has_perm('users.generate_report'):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            stats = {
                'total_users': User.objects.count(),
                'students': User.objects.filter(role='student').count(),
                'teachers': User.objects.filter(role='teacher').count(),
                'managers': User.objects.filter(role='manager').count(),
            }
            return Response(stats)

        elif action == "report-overview":
            """
            Báo cáo tổng quan về người dùng, phòng học, đặt phòng, và thiết bị.
            """
            if not request.user.has_perm('users.generate_report'):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            current_time = timezone.now()

            # Thống kê người dùng
            user_stats = {
                'total_users': User.objects.count(),
                'students': User.objects.filter(role='student').count(),
                'teachers': User.objects.filter(role='teacher').count(),
                'managers': User.objects.filter(role='manager').count(),
                'bookings_by_students': Booking.objects.filter(user__role='student').count(),
                'bookings_by_teachers': Booking.objects.filter(user__role='teacher').count(),
            }

            # Thống kê phòng học
            space_stats = {
                'total_spaces': StudySpace.objects.count(),
                'individual_spaces': StudySpace.objects.filter(space_type='INDIVIDUAL').count(),
                'group_spaces': StudySpace.objects.filter(space_type='GROUP').count(),
                'mentoring_spaces': StudySpace.objects.filter(space_type='MENTORING').count(),
                'empty_spaces': sum(1 for space in StudySpace.objects.all() if space.get_space_status(current_time) == 'EMPTY'),
                'booked_spaces': sum(1 for space in StudySpace.objects.all() if space.get_space_status(current_time) == 'BOOKED'),
                'inuse_spaces': sum(1 for space in StudySpace.objects.all() if space.get_space_status(current_time) == 'INUSE'),
            }

            # Thống kê đặt phòng (tổng quan)
            booking_stats = {
                'total_bookings': Booking.objects.count(),
                'confirmed_bookings': Booking.objects.filter(status='CONFIRMED').count(),
                'check_in_bookings': Booking.objects.filter(status='CHECK_IN').count(),
                'check_out_bookings': Booking.objects.filter(status='CHECK_OUT').count(),
                'cancelled_bookings': Booking.objects.filter(status='CANCELLED').count(),
            }

            # Thống kê thiết bị
            equipment_stats = {
                'total_equipments': Equipment.objects.count(),
                'available_equipments': Equipment.objects.filter(status='AVAILABLE').count(),
                'borrowed_equipments': Equipment.objects.filter(status='BORROWED').count(),
                'broken_equipments': Equipment.objects.filter(status='BROKEN').count(),
                'maintenance_equipments': Equipment.objects.filter(status='MAINTENANCE').count(),
            }

            return Response({
                'users': user_stats,
                'spaces': space_stats,
                'bookings': booking_stats,
                'equipments': equipment_stats,
                'generated_at': current_time.isoformat(),
            })

        elif action == "report-detailed":
            """
            Báo cáo chi tiết theo khoảng thời gian.
            - Query params: start_time, end_time (ISO format, ví dụ: 2025-05-01T00:00:00Z).
            """
            if not request.user.has_perm('users.generate_report'):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Lấy khoảng thời gian từ query params
            start_time_str = request.query_params.get('start_time')
            end_time_str = request.query_params.get('end_time')

            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00')) if start_time_str else timezone.now() - timedelta(days=30)
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00')) if end_time_str else timezone.now()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use ISO format (e.g., 2025-05-01T00:00:00Z).'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if start_time >= end_time:
                return Response(
                    {'error': 'start_time must be before end_time.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Thống kê đặt phòng trong khoảng thời gian
            bookings_in_range = Booking.objects.filter(
                start_time__gte=start_time,
                end_time__lte=end_time
            )

            booking_stats = {
                'total_bookings': bookings_in_range.count(),
                'confirmed_bookings': bookings_in_range.filter(status='CONFIRMED').count(),
                'check_in_bookings': bookings_in_range.filter(status='CHECK_IN').count(),
                'check_out_bookings': bookings_in_range.filter(status='CHECK_OUT').count(),
                'cancelled_bookings': bookings_in_range.filter(status='CANCELLED').count(),
                'bookings_by_students': bookings_in_range.filter(user__role='student').count(),
                'bookings_by_teachers': bookings_in_range.filter(user__role='teacher').count(),
            }

            # Thống kê tỷ lệ sử dụng phòng học
            total_hours = (end_time - start_time).total_seconds() / 3600  # Tổng số giờ trong khoảng thời gian
            total_spaces = StudySpace.objects.count()
            total_available_space_hours = total_hours * total_spaces  # Tổng số giờ-phòng khả dụng

            used_space_hours = 0
            for booking in bookings_in_range.exclude(status='CANCELLED'):
                duration = (booking.end_time - booking.start_time).total_seconds() / 3600
                used_space_hours += duration

            utilization_rate = (used_space_hours / total_available_space_hours * 100) if total_available_space_hours > 0 else 0

            space_stats = {
                'total_spaces': total_spaces,
                'individual_spaces': StudySpace.objects.filter(space_type='INDIVIDUAL').count(),
                'group_spaces': StudySpace.objects.filter(space_type='GROUP').count(),
                'mentoring_spaces': StudySpace.objects.filter(space_type='MENTORING').count(),
                'utilization_rate_percent': round(utilization_rate, 2),
                'total_space_hours_used': round(used_space_hours, 2),
                'total_space_hours_available': round(total_available_space_hours, 2),
            }

            # Thống kê thiết bị trong khoảng thời gian
            equipments_in_range = Equipment.objects.filter(
                booking__start_time__gte=start_time,
                booking__end_time__lte=end_time
            )

            equipment_stats = {
                'total_equipments_borrowed': equipments_in_range.filter(status='BORROWED').count(),
                'broken_equipments': equipments_in_range.filter(status='BROKEN').count(),
                'maintenance_equipments': equipments_in_range.filter(status='MAINTENANCE').count(),
            }

            return Response({
                'time_range': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                },
                'bookings': booking_stats,
                'spaces': space_stats,
                'equipments': equipment_stats,
                'generated_at': timezone.now().isoformat(),
            })

    def put(self, request, action=None):
        if action == "profile":
            """
            Cập nhật profile của ban quản lý.
            """
            serializer = ManagerProfileSerializer(
                request.user.manager_profile,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)