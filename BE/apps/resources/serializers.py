from rest_framework import serializers
from .models import StudySpace
from apps.bookings.models import Booking
from apps.bookings.serializers import BookingSerializer


class StudySpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySpace
        fields = ['id', 'name', 'capacity', 'space_type', 'space_status']

    def validate(self, data):
        if data['capacity'] <= 0:
            raise serializers.ValidationError("Sức chứa phải lớn hơn 0.")
        return data

class StudySpaceUsageSerializer(serializers.ModelSerializer):
    current_status = serializers.SerializerMethodField()
    bookings_today = serializers.SerializerMethodField()

    class Meta:
        model = StudySpace
        fields = ['id', 'name', 'capacity', 'space_type', 'current_status', 'bookings_today']

    def get_current_status(self, obj):
        current_time = self.context['current_time']
        return obj.get_space_status(current_time)

    def get_bookings_today(self, obj):
        current_time = self.context['current_time']
        end_of_day = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        bookings = Booking.objects.filter(
            space=obj,
            start_time__gte=current_time,
            start_time__lte=end_of_day,
            status__in=['CONFIRMED', 'CHECK_IN']  # Chỉ lấy các đặt phòng chưa kết thúc
        ).order_by('start_time')
        return BookingSerializer(bookings, many=True, context={'request': self.context['request']}).data
