from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import Feedback, Notification , NotificationReadStatus, Comment
from .serializers import FeedbackSerializer, FeedbackCreateSerializer, NotificationSerializer, NotificationCreateSerializer, CommentSerializer
from .permissions import IsStudentOrTeacher, IsManager, IsSenderOrManager, IsManagerForNotification, CanCommentOnFeedback
from django.db import models

class FeedbackCreateView(APIView):
    """
    API để sinh viên hoặc giảng viên gửi phản hồi.
    - POST /api/messages/feedbacks/
    """
    permission_classes = [IsStudentOrTeacher]

    def post(self, request):
        serializer = FeedbackCreateSerializer(data=request.data)
        if serializer.is_valid():
            feedback = serializer.save(sender=request.user)
            return Response(FeedbackSerializer(feedback).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FeedbackListView(APIView):
    """
    API để xem danh sách phản hồi.
    - GET /api/messages/feedbacks/list/
    - Sinh viên/Giảng viên: Xem phản hồi của chính họ.
    - Ban quản lý: Xem tất cả phản hồi.
    """
    permission_classes = [IsSenderOrManager]

    def get(self, request):
        if request.user.role == 'manager':
            feedbacks = Feedback.objects.all()
        else:
            feedbacks = Feedback.objects.filter(sender=request.user)
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)

class FeedbackRespondView(APIView):
    """
    API để ban quản lý trả lời phản hồi.
    - PUT /api/messages/feedbacks/<id>/respond/
    """
    permission_classes = [IsManager]

    def put(self, request, pk):
        try:
            feedback = Feedback.objects.get(pk=pk)
        except Feedback.DoesNotExist:
            return Response({'error': 'Feedback not found'}, status=status.HTTP_404_NOT_FOUND)

        response_text = request.data.get('response')
        if not response_text:
            return Response({'error': 'Response text is required'}, status=status.HTTP_400_BAD_REQUEST)

        feedback.response = response_text
        feedback.status = 'responded'
        feedback.responded_by = request.user
        feedback.save()

        return Response(FeedbackSerializer(feedback).data)

class FeedbackMarkReadView(APIView):
    """
    API để đánh dấu phản hồi là đã đọc.
    - POST /api/feedback/<id>/mark-read/
    """
    permission_classes = [IsSenderOrManager]

    def post(self, request, pk):
        try:
            feedback = Feedback.objects.get(pk=pk)
        except Feedback.DoesNotExist:
            return Response({'error': 'Feedback not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role != 'manager' and feedback.sender != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        feedback.is_read = True
        feedback.save()
        return Response({'message': 'Feedback marked as read'})

class CommentCreateView(APIView):
    """
    API để thêm bình luận dưới một phản hồi.
    - POST /api/feedback/<id>/comments/
    """
    permission_classes = [CanCommentOnFeedback]

    def post(self, request, pk):
        try:
            feedback = Feedback.objects.get(pk=pk)
        except Feedback.DoesNotExist:
            return Response({'error': 'Feedback not found'}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra quyền bình luận
        if request.user.role != 'manager' and feedback.sender != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content')
        if not content:
            return Response({'error': 'Comment content is required'}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(
            feedback=feedback,
            sender=request.user,
            content=content
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

class FeedbackCommentsList(APIView):
    """
    API endpoint để hiển thị tất cả bình luận của một phản hồi cụ thể
    cho người gửi phản hồi và quản trị viên.
    - GET /api/feedback/<int:feedback_pk>/all-comments/
    """
    permission_classes = [CanCommentOnFeedback]

    def get(self, request, pk):
        try:
            feedback = Feedback.objects.get(pk=pk)
        except Feedback.DoesNotExist:
            return Response({'error': 'Không tìm thấy phản hồi.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_sender = (feedback.sender == user)
        is_manager = (request.user.role == 'manager') 

        if is_sender or is_manager:
            comments = Comment.objects.filter(feedback=feedback).order_by('created_at')
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': 'Bạn không có quyền xem tất cả bình luận của phản hồi này.'}, status=status.HTTP_403_FORBIDDEN)

"""
CHỨC NĂNG THÔNG BÁO
"""
class NotificationCreateView(APIView):
    """
    API để ban quản lý gửi thông báo.
    - POST /api/messages/notifications/
    """
    permission_classes = [IsManagerForNotification]

    def post(self, request):
        serializer = NotificationCreateSerializer(data=request.data)
        if serializer.is_valid():
            notification = serializer.save(sender=request.user)
            # Truyền context khi khởi tạo NotificationSerializer
            return Response(NotificationSerializer(notification, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class NotificationListView(APIView):
#     """
#     API để người dùng xem thông báo của họ.
#     - GET /api/messages/notifications/
#     """
#     pagination_class = PageNumberPagination

#     def get(self, request):
#         user = request.user
#         if not user.is_authenticated:
#             return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

#         notifications = Notification.objects.filter(
#             models.Q(target_type='all') |
#             models.Q(target_type=user.role) |
#             models.Q(target_type='specific_user', target_user=user)
#         ).distinct()

#         paginator = self.pagination_class()
#         page = paginator.paginate_queryset(notifications, request)
#         serializer = NotificationSerializer(page, many=True, context={'request': request})
#         return paginator.get_paginated_response(serializer.data)

class NotificationListView(ListAPIView):
    pagination_class = PageNumberPagination
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            # Trả về một queryset rỗng nếu user chưa đăng nhập
            # (sẽ được xử lý trong get())
            return Notification.objects.none()

        return Notification.objects.filter(
            models.Q(target_type='all') |
            models.Q(target_type=user.role) |
            models.Q(target_type='specific_user', target_user=user)
        ).distinct()

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        return super().get(request, *args, **kwargs)

class NotificationMarkReadView(APIView):
    """
    API để đánh dấu thông báo là đã đọc.
    - POST /api/feedback/notifications/<id>/mark-read/
    """
    def post(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra xem user có quyền xem thông báo này không
        if not (notification.target_type == 'all' or
                notification.target_type == user.role or
                (notification.target_type == 'specific_user' and notification.target_user == user)):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        read_status, created = NotificationReadStatus.objects.get_or_create(user=user, notification=notification)
        read_status.is_read = True
        read_status.save()
        return Response({'message': 'Notification marked as read'})

class NewFeedbackNotificationCountView(APIView):
    """
    API để kiểm tra số lượng phản hồi và thông báo mới chưa đọc.
    - GET /api/feedback/new-count/
    """
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        # Số lượng phản hồi chưa đọc
        feedback_count = 0
        if user.role in ['student', 'teacher']:
            feedback_count = Feedback.objects.filter(sender=user, is_read=False).count()

        # Số lượng thông báo chưa đọc
        notifications = Notification.objects.filter(
            models.Q(target_type='all') |
            models.Q(target_type=user.role) |
            models.Q(target_type='specific_user', target_user=user)
        ).distinct()
        notification_count = 0
        for notification in notifications:
            read_status = notification.read_statuses.filter(user=user).first()
            if not read_status or not read_status.is_read:
                notification_count += 1

        return Response({
            'new_feedbacks': feedback_count,
            'new_notifications': notification_count
        })