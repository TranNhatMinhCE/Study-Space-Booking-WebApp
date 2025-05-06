from django.urls import path
from . import views

urlpatterns = [
    path('study-spaces/', views.StudySpaceListCreateAPIView.as_view(), name='study_space_list'),
    path('get-space-status/<int:room_id>/', views.get_space_status, name='get_space_status'),
    path('search-available-spaces/', views.search_available_spaces, name='search_available_spaces'),
    path('study-spaces/<int:pk>/', views.StudySpaceRetrieveUpdateDestroyAPIView.as_view(), name='study_space_detail'),
    path('spaces-usage/', views.SpacesUsageAPIView.as_view(), name='spaces-usage'),
]