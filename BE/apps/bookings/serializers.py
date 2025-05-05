from rest_framework import serializers
from .models import  Booking, Equipment, EquipmentType
from apps.resources.models import StudySpace



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
    space_name = serializers.CharField(source='space.name', read_only=True)  # Hiển thị tên của space
    space_id = serializers.PrimaryKeyRelatedField(
        queryset=StudySpace.objects.all(), source='space', write_only=True
    )  # Nhận ID khi tạo
    user = serializers.StringRelatedField(read_only=True)
    equipments = EquipmentSerializer(many=True, read_only=True)
    equipment_requests = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Booking
        fields = ['id', 'user', 'space_name', 'space_id', 'start_time', 'end_time', 'status', 'equipments', 'equipment_requests']

    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Thời gian bắt đầu phải trước thời gian kết thúc.")
        return data