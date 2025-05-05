from rest_framework import generics
from .models import StudySpace
from .serializers import StudySpaceSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
# Create your views here.
class StudySpaceListCreateAPIView(generics.ListCreateAPIView):
    queryset = StudySpace.objects.all()
    serializer_class = StudySpaceSerializer


@api_view(['GET'])
def get_space_status(request, space_id):
    try:
        space = StudySpace.objects.get(id=space_id)
        at_time = request.GET.get('at_time', timezone.now())
        status = space.get_space_status(at_time)
        return Response({'status': status})
    except StudySpace.DoesNotExist:
        return Response({'error': 'Space not found'}, status=404)