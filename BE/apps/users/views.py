from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserSerializer, StudentProfileSerializer, TeacherProfileSerializer, ManagerProfileSerializer
from .permissions import HasViewOwnProfilePermission, HasEditOwnProfilePermission, HasViewAllUsersPermission, HasGenerateReportPermission, IsOwnProfile
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken

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

# Class con: ManagerAPIView
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