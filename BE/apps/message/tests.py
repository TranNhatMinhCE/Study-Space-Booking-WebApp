from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from .models import Feedback, Comment, Notification, NotificationReadStatus
from .admin import FeedbackAdmin, CommentAdmin, NotificationAdmin, NotificationReadStatusAdmin
from apps.users.models import StudentProfile, TeacherProfile, ManagerProfile

User = get_user_model()

class FeedbackTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_site = AdminSite()

        # Tạo user
        self.student = User.objects.create_user(
            username='student1',
            email='student1@hcmut.edu.vn',
            password='password123',
            role='student',
            first_name='Nguyen',
            last_name='Van A',
            user_id='123456'
        )
        StudentProfile.objects.create(user=self.student, major='Computer Science')

        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@hcmut.edu.vn',
            password='password123',
            role='teacher',
            first_name='Tran',
            last_name='Thi B',
            user_id='TCH001'
        )
        TeacherProfile.objects.create(user=self.teacher, department='IT')

        self.manager1 = User.objects.create_user(
            username='manager1',
            email='manager1@hcmut.edu.vn',
            password='password123',
            role='manager',
            first_name='Manager',
            last_name='One',
            user_id='MGR001'
        )
        ManagerProfile.objects.create(user=self.manager1, role_description='Manager')

        self.manager2 = User.objects.create_user(
            username='manager2',
            email='manager2@hcmut.edu.vn',
            password='password123',
            role='manager',
            first_name='Manager',
            last_name='Two',
            user_id='MGR002'
        )
        ManagerProfile.objects.create(user=self.manager2, role_description='Manager')

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_student_can_create_feedback(self):
        """Kiểm tra sinh viên có thể gửi phản hồi"""
        self.authenticate(self.student)
        response = self.client.post(reverse('feedback-create'), {'content': 'Hệ thống cần cải thiện.'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 1)
        self.assertEqual(Feedback.objects.first().sender, self.student)

    def test_teacher_can_create_feedback(self):
        """Kiểm tra giảng viên có thể gửi phản hồi"""
        self.authenticate(self.teacher)
        response = self.client.post(reverse('feedback-create'), {'content': 'Cần thêm tài liệu học tập.'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 1)
        self.assertEqual(Feedback.objects.first().sender, self.teacher)

    def test_manager_cannot_create_feedback(self):
        """Kiểm tra ban quản lý không thể gửi phản hồi"""
        self.authenticate(self.manager1)
        response = self.client.post(reverse('feedback-create'), {'content': 'Tôi muốn gửi phản hồi.'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_view_own_feedback(self):
        """Kiểm tra sinh viên chỉ thấy phản hồi của họ"""
        Feedback.objects.create(sender=self.student, content='Phản hồi của sinh viên')
        Feedback.objects.create(sender=self.teacher, content='Phản hồi của giảng viên')
        self.authenticate(self.student)
        response = self.client.get(reverse('feedback-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sender']['username'], 'student1')

    def test_manager_can_view_all_feedbacks(self):
        """Kiểm tra ban quản lý thấy tất cả phản hồi"""
        Feedback.objects.create(sender=self.student, content='Phản hồi của sinh viên')
        Feedback.objects.create(sender=self.teacher, content='Phản hồi của giảng viên')
        self.authenticate(self.manager1)
        response = self.client.get(reverse('feedback-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_manager_can_respond_to_feedback(self):
        """Kiểm tra ban quản lý có thể trả lời phản hồi"""
        feedback = Feedback.objects.create(sender=self.student, content='Hệ thống cần cải thiện.')
        self.authenticate(self.manager1)
        response = self.client.put(reverse('feedback-respond', args=[feedback.id]), {'response': 'Chúng tôi sẽ xem xét.'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, 'responded')
        self.assertEqual(feedback.response, 'Chúng tôi sẽ xem xét.')
        self.assertEqual(feedback.responded_by, self.manager1)

    def test_student_cannot_respond_to_feedback(self):
        """Kiểm tra sinh viên không thể trả lời phản hồi"""
        feedback = Feedback.objects.create(sender=self.student, content='Hệ thống cần cải thiện.')
        self.authenticate(self.student)
        response = self.client.put(reverse('feedback-respond', args=[feedback.id]), {'response': 'Tôi muốn trả lời.'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_mark_feedback_as_read(self):
        """Kiểm tra sinh viên có thể đánh dấu phản hồi là đã đọc"""
        feedback = Feedback.objects.create(sender=self.student, content='Hệ thống cần cải thiện.')
        self.authenticate(self.student)
        response = self.client.post(reverse('feedback-mark-read', args=[feedback.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        feedback.refresh_from_db()
        self.assertTrue(feedback.is_read)

    def test_manager_can_mark_feedback_as_read(self):
        """Kiểm tra ban quản lý có thể đánh dấu phản hồi là đã đọc"""
        feedback = Feedback.objects.create(sender=self.student, content='Hệ thống cần cải thiện.')
        self.authenticate(self.manager1)
        response = self.client.post(reverse('feedback-mark-read', args=[feedback.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        feedback.refresh_from_db()
        self.assertTrue(feedback.is_read)

    def test_student_can_comment_on_own_feedback(self):
        """Kiểm tra sinh viên có thể bình luận dưới phản hồi của họ"""
        feedback = Feedback.objects.create(sender=self.student, content='Hệ thống cần cải thiện.')
        self.authenticate(self.student)
        response = self.client.post(reverse('comment-create', args=[feedback.id]), {'content': 'Cần thêm tối ưu hóa.'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().sender, self.student)

    def test_manager_can_comment_on_feedback(self):
        """Kiểm tra ban quản lý có thể bình luận dưới phản hồi"""
        feedback = Feedback.objects.create(sender=self.student, content='Hệ thống cần cải thiện.')
        self.authenticate(self.manager1)
        response = self.client.post(reverse('comment-create', args=[feedback.id]), {'content': 'Chúng tôi sẽ xem xét.'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().sender, self.manager1)

    def test_multiple_managers_can_comment_on_feedback(self):
        """Kiểm tra nhiều quản lý có thể bình luận dưới một phản hồi"""
        feedback = Feedback.objects.create(sender=self.student, content='Hệ thống cần cải thiện.')
        self.authenticate(self.manager1)
        self.client.post(reverse('comment-create', args=[feedback.id]), {'content': 'Cảm ơn ý kiến.'})
        self.authenticate(self.manager2)
        response = self.client.post(reverse('comment-create', args=[feedback.id]), {'content': 'Tôi đồng ý.'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)

    def test_teacher_cannot_comment_on_student_feedback(self):
        """Kiểm tra giảng viên không thể bình luận dưới phản hồi của sinh viên"""
        feedback = Feedback.objects.create(sender=self.student, content='Hệ thống cần cải thiện.')
        self.authenticate(self.teacher)
        response = self.client.post(reverse('comment-create', args=[feedback.id]), {'content': 'Tôi muốn bình luận.'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_new_feedback_count(self):
        """Kiểm tra API đếm số phản hồi mới chưa đọc"""
        Feedback.objects.create(sender=self.student, content='Phản hồi 1', is_read=False)
        Feedback.objects.create(sender=self.student, content='Phản hồi 2', is_read=True)
        self.authenticate(self.student)
        response = self.client.get(reverse('new-feedback-notification-count'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_feedbacks'], 1)

class NotificationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_site = AdminSite()

        self.student = User.objects.create_user(
            username='student1',
            email='student1@hcmut.edu.vn',
            password='password123',
            role='student',
            first_name='Nguyen',
            last_name='Van A',
            user_id='123456'
        )
        StudentProfile.objects.create(user=self.student, major='Computer Science')

        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@hcmut.edu.vn',
            password='password123',
            role='teacher',
            first_name='Tran',
            last_name='Thi B',
            user_id='TCH001'
        )
        TeacherProfile.objects.create(user=self.teacher, department='IT')

        self.manager1 = User.objects.create_user(
            username='manager1',
            email='manager1@hcmut.edu.vn',
            password='password123',
            role='manager',
            first_name='Manager',
            last_name='One',
            user_id='MGR001'
        )
        ManagerProfile.objects.create(user=self.manager1, role_description='Manager')

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_manager_can_send_notification_to_all(self):
        """Kiểm tra ban quản lý có thể gửi thông báo đến tất cả người dùng"""
        self.authenticate(self.manager1)
        response = self.client.post(reverse('notification-create'), {
            'target_type': 'all',
            'content': 'Hệ thống sẽ bảo trì.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationReadStatus.objects.count(), 3)  # student, teacher, manager

    def test_manager_can_send_notification_to_role(self):
        """Kiểm tra ban quản lý có thể gửi thông báo đến một nhóm"""
        self.authenticate(self.manager1)
        response = self.client.post(reverse('notification-create'), {
            'target_type': 'student',
            'content': 'Kỳ thi sắp tới.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationReadStatus.objects.count(), 1)  # Chỉ student

    def test_manager_can_send_notification_to_specific_user(self):
        """Kiểm tra ban quản lý có thể gửi thông báo đến một người dùng cụ thể"""
        self.authenticate(self.manager1)
        response = self.client.post(reverse('notification-create'), {
            'target_type': 'specific_user',
            'target_user': self.student.id,
            'content': 'Nộp báo cáo trước ngày 12/05.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationReadStatus.objects.count(), 1)
        self.assertEqual(NotificationReadStatus.objects.first().user, self.student)

    def test_student_cannot_send_notification(self):
        """Kiểm tra sinh viên không thể gửi thông báo"""
        self.authenticate(self.student)
        response = self.client.post(reverse('notification-create'), {
            'target_type': 'all',
            'content': 'Tôi muốn gửi thông báo.'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_view_notifications(self):
        """Kiểm tra sinh viên có thể xem thông báo của họ"""
        notification1 = Notification.objects.create(sender=self.manager1, target_type='all', content='Thông báo cho tất cả')
        notification2 = Notification.objects.create(sender=self.manager1, target_type='student', content='Thông báo cho sinh viên')
        notification3 = Notification.objects.create(sender=self.manager1, target_type='specific_user', target_user=self.student, content='Thông báo cho student1')
        NotificationReadStatus.objects.create(user=self.student, notification=notification1)
        NotificationReadStatus.objects.create(user=self.student, notification=notification2)
        NotificationReadStatus.objects.create(user=self.student, notification=notification3)
        self.authenticate(self.student)
        response = self.client.get(reverse('notification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_teacher_cannot_view_student_specific_notification(self):
        """Kiểm tra giảng viên không thấy thông báo dành riêng cho sinh viên"""
        notification1 = Notification.objects.create(sender=self.manager1, target_type='all', content='Thông báo cho tất cả')
        notification2 = Notification.objects.create(sender=self.manager1, target_type='student', content='Thông báo cho sinh viên')
        NotificationReadStatus.objects.create(user=self.student, notification=notification1)
        NotificationReadStatus.objects.create(user=self.student, notification=notification2)
        NotificationReadStatus.objects.create(user=self.teacher, notification=notification1)
        self.authenticate(self.teacher)
        response = self.client.get(reverse('notification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['target_type'], 'all')

    def test_student_can_mark_notification_as_read(self):
        """Kiểm tra sinh viên có thể đánh dấu thông báo là đã đọc"""
        notification = Notification.objects.create(sender=self.manager1, target_type='specific_user', target_user=self.student, content='Thông báo cho student1')
        read_status = NotificationReadStatus.objects.create(user=self.student, notification=notification, is_read=False)
        self.authenticate(self.student)
        response = self.client.post(reverse('notification-mark-read', args=[notification.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        read_status.refresh_from_db()
        self.assertTrue(read_status.is_read)

    def test_new_notification_count(self):
        """Kiểm tra API đếm số thông báo mới chưa đọc"""
        notification1 = Notification.objects.create(sender=self.manager1, target_type='all', content='Thông báo 1')
        notification2 = Notification.objects.create(sender=self.manager1, target_type='student', content='Thông báo 2')
        NotificationReadStatus.objects.create(user=self.student, notification=notification1, is_read=False)
        NotificationReadStatus.objects.create(user=self.student, notification=notification2, is_read=True)
        self.authenticate(self.student)
        response = self.client.get(reverse('new-feedback-notification-count'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_notifications'], 1)

    def test_notification_pagination(self):
        """Kiểm tra phân trang cho danh sách thông báo"""
        for i in range(15):
            notification = Notification.objects.create(
                sender=self.manager1,
                target_type='all',
                content=f'Thông báo {i}'
            )
            NotificationReadStatus.objects.create(user=self.student, notification=notification)
        self.authenticate(self.student)
        response = self.client.get(reverse('notification-list') + '?page=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Mặc định page_size=10
        self.assertIsNotNone(response.data['next'])

class AdminTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_site = AdminSite()

        self.student = User.objects.create_user(
            username='student1',
            email='student1@hcmut.edu.vn',
            password='password123',
            role='student',
            first_name='Nguyen',
            last_name='Van A',
            user_id='123456'
        )
        StudentProfile.objects.create(user=self.student, major='Computer Science')

        self.manager1 = User.objects.create_user(
            username='manager1',
            email='manager1@hcmut.edu.vn',
            password='password123',
            role='manager',
            first_name='Manager',
            last_name='One',
            user_id='MGR001'
        )
        ManagerProfile.objects.create(user=self.manager1, role_description='Manager')

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )

    def test_feedback_admin_queryset_superuser(self):
        """Kiểm tra superuser thấy tất cả phản hồi trong admin"""
        Feedback.objects.create(sender=self.student, content='Phản hồi 1')
        feedback_admin = FeedbackAdmin(Feedback, self.admin_site)
        request = self.client.request().wsgi_request
        request.user = self.superuser
        qs = feedback_admin.get_queryset(request)
        self.assertEqual(qs.count(), 1)

    def test_feedback_admin_queryset_manager(self):
        """Kiểm tra ban quản lý thấy tất cả phản hồi trong admin"""
        Feedback.objects.create(sender=self.student, content='Phản hồi 1')
        feedback_admin = FeedbackAdmin(Feedback, self.admin_site)
        request = self.client.request().wsgi_request
        request.user = self.manager1
        qs = feedback_admin.get_queryset(request)
        self.assertEqual(qs.count(), 1)

    def test_feedback_admin_queryset_student(self):
        """Kiểm tra sinh viên không thấy phản hồi trong admin"""
        Feedback.objects.create(sender=self.student, content='Phản hồi 1')
        feedback_admin = FeedbackAdmin(Feedback, self.admin_site)
        request = self.client.request().wsgi_request
        request.user = self.student
        qs = feedback_admin.get_queryset(request)
        self.assertEqual(qs.count(), 0)

    def test_comment_admin_queryset_superuser(self):
        """Kiểm tra superuser thấy tất cả bình luận trong admin"""
        feedback = Feedback.objects.create(sender=self.student, content='Phản hồi 1')
        Comment.objects.create(feedback=feedback, sender=self.student, content='Bình luận 1')
        comment_admin = CommentAdmin(Comment, self.admin_site)
        request = self.client.request().wsgi_request
        request.user = self.superuser
        qs = comment_admin.get_queryset(request)
        self.assertEqual(qs.count(), 1)

    def test_comment_admin_queryset_manager(self):
        """Kiểm tra ban quản lý thấy tất cả bình luận trong admin"""
        feedback = Feedback.objects.create(sender=self.student, content='Phản hồi 1')
        Comment.objects.create(feedback=feedback, sender=self.student, content='Bình luận 1')
        comment_admin = CommentAdmin(Comment, self.admin_site)
        request = self.client.request().wsgi_request
        request.user = self.manager1
        qs = comment_admin.get_queryset(request)
        self.assertEqual(qs.count(), 1)

    def test_notification_admin_queryset_superuser(self):
        """Kiểm tra superuser thấy tất cả thông báo trong admin"""
        Notification.objects.create(sender=self.manager1, target_type='all', content='Thông báo 1')
        notification_admin = NotificationAdmin(Notification, self.admin_site)
        request = self.client.request().wsgi_request
        request.user = self.superuser
        qs = notification_admin.get_queryset(request)
        self.assertEqual(qs.count(), 1)