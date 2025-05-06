from django.urls import path
from .views import UserAPIView, StudentAPIView, TeacherAPIView, ManagerAPIView

urlpatterns = [
    # Các endpoint chung
    path('<str:action>/', UserAPIView.as_view(), name='user_action'),
    # Endpoint cho sinh viên
    path('student/<str:action>/', StudentAPIView.as_view(), name='student_action'),
    # Endpoint cho giảng viên
    path('teacher/<str:action>/', TeacherAPIView.as_view(), name='teacher_action'),
    # Endpoint cho ban quản lý
    path('manager/<str:action>/', ManagerAPIView.as_view(), name='manager_action'),
]



