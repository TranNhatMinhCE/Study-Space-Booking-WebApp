from rest_framework import serializers
from .models import Booking, Equipment, EquipmentType
from apps.resources.models import StudySpace
from django.utils import timezone

class EquipmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentType
        fields = ['id', 'name', 'description', 'total_quantity']

class EquipmentSerializer(serializers.ModelSerializer):
    equipment_type = EquipmentTypeSerializer(read_only=True)
    equipment_type_id = serializers.PrimaryKeyRelatedField(
        queryset=EquipmentType.objects.all(), source='equipment_type', write_only=True
    )

    class Meta:
        model = Equipment
        fields = ['id', 'equipment_type', 'equipment_type_id', 'status', 'booking']

class BookingSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name', read_only=True)
    space_id = serializers.PrimaryKeyRelatedField(
        queryset=StudySpace.objects.all(), source='space', write_only=True
    )
    user = serializers.StringRelatedField(read_only=True)
    equipments = EquipmentSerializer(many=True, read_only=True)
    equipment_requests = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )
    qr_code_url = serializers.SerializerMethodField()  # Thêm trường để trả về URL mã QR

    class Meta:
        model = Booking
        fields = ['id', 'user', 'space_name', 'space_id', 'start_time', 'end_time', 'status', 'equipments', 'equipment_requests', 'qr_code_url']

    def get_qr_code_url(self, obj):
        """Trả về URL của hình ảnh mã QR"""
        if hasattr(obj, 'qr_code') and obj.qr_code.image:
            return self.context['request'].build_absolute_uri(obj.qr_code.image.url)
        return None

    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Thời gian bắt đầu phải trước thời gian kết thúc.")
        if data['start_time'] < timezone.now():
            raise serializers.ValidationError("Không thể đặt phòng trong quá khứ.")
        return data