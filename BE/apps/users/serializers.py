from rest_framework import serializers
from .models import User, StudentProfile, TeacherProfile, ManagerProfile

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer cho model User.
    - Dùng để serialize thông tin chung của người dùng.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name',
                   'user_id', 'phone_number', 'address', 'created_at', 'updated_at']
    
class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho StudentProfile.
    - Bao gồm thông tin từ User thông qua trường user.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = ['user', 'major']

class TeacherProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho TeacherProfile.
    - Bao gồm thông tin từ User thông qua trường user.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ['user', 'department']

class ManagerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho ManagerProfile.
    - Bao gồm thông tin từ User thông qua trường user.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = ManagerProfile
        fields = ['user', 'role_description']

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer cho việc đăng ký người dùng.
    - Xử lý tạo User và Profile tương ứng dựa trên role.
    """
    password = serializers.CharField(write_only=True, min_length=8)  # Mật khẩu, yêu cầu tối thiểu 8 ký tự
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, write_only=True)  # Vai trò
    major = serializers.CharField(required=False, write_only=True)  # Ngành học (cho sinh viên)
    department = serializers.CharField(required=False, write_only=True)  # Khoa (cho giảng viên)
    role_description = serializers.CharField(required=False, write_only=True)  # Mô tả vai trò (cho ban quản lý)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'first_name', 'last_name', 
                  'user_id', 'major', 'department', 'role_description']

    def validate(self, data):
        """
        Kiểm tra dữ liệu đầu vào.
        - Sinh viên phải có user_id.
        - Giảng viên và ban quản lý cũng phải có user_id.
        """
        role = data.get('role')
        if role == 'student' and not data.get('user_id'):
            raise serializers.ValidationError("Student ID is required for students.")
        if role in ['teacher', 'manager'] and not data.get('user_id'):
            raise serializers.ValidationError("Staff ID is required for teachers and managers.")
        return data

    def create(self, validated_data):
        """
        Tạo User và Profile tương ứng.
        - Tạo User trước, sau đó tạo Profile dựa trên role.
        """
        role = validated_data.pop('role')
        major = validated_data.pop('major', None)
        department = validated_data.pop('department', None)
        role_description = validated_data.pop('role_description', None)

        # Tạo user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=role,
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            user_id=validated_data['user_id'],
        )

        # Tạo profile tương ứng
        if role == 'student':
            StudentProfile.objects.create(user=user, major=major)
        elif role == 'teacher':
            TeacherProfile.objects.create(user=user, department=department)
        elif role == 'manager':
            ManagerProfile.objects.create(user=user, role_description=role_description)

        return user