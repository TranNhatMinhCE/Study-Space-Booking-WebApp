from django.urls import path
from . import views

urlpatterns = [
    path('study-spaces/', views.StudySpaceListCreateAPIView.as_view(), name='study_space_list'),
    path('get-space-status/<int:room_id>/', views.get_space_status, name='get_space_status'),
]