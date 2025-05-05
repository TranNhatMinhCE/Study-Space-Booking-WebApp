from django.db import models
from django.utils import timezone

# Định nghĩa choices cho space_type
SPACE_TYPE_CHOICES = [
    ('INDIVIDUAL', 'Individual'),
    ('GROUP', 'Group'),
    ('MENTORING', 'Mentoring'),
]

# Định nghĩa choices cho space_status
SPACE_STATUS_CHOICES = [
    ('EMPTY', 'Empty'),
    ('BOOKED', 'Booked'),
    ('INUSE', 'In Use'),
]

class StudySpace(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.IntegerField()
    space_type = models.CharField(
        max_length=20,
        choices=SPACE_TYPE_CHOICES,  # Sử dụng danh sách tuple
        default='INDIVIDUAL'
    )
    space_status = models.CharField(
        max_length=20,
        choices=SPACE_STATUS_CHOICES,  # Sử dụng danh sách tuple
        default='EMPTY'
    )

    def __str__(self):
        return f"{self.name}"

    def get_space_status(self, at_time):
        from apps.bookings.models import Booking, SPACE_STATUS_MAPPING
        current_bookings = Booking.objects.filter(
            space=self,
            start_time__lte=at_time,
            end_time__gt=at_time,
        ).exclude(status='CANCELLED')
        if current_bookings.exists():
            booking = current_bookings.first()
            return SPACE_STATUS_MAPPING.get(booking.status, 'EMPTY')
        return self.space_status