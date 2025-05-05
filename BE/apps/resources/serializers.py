from rest_framework import serializers
from .models import StudySpace 

class StudySpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySpace
        fields = ['id', 'name', 'capacity', 'space_type', 'space_status']

    def validate(self, data):
        if data['capacity'] <= 0:
            raise serializers.ValidationError("Sức chứa phải lớn hơn 0.")
        return data