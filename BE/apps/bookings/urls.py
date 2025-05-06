from django.urls import path
from . import views

urlpatterns = [
    path('bookings/', views.BookingListCreateAPIView.as_view(), name='booking_list'),
    path('equipment-types/', views.EquipmentTypeListCreateAPIView.as_view(), name='equipment_type_list'),
    path('scan-qr/', views.scan_qr_code, name='scan_qr'),
    path('update-booking-status/', views.update_booking_status_view, name='update_booking_status'),
    path('<int:booking_id>/cancel/', views.cancel_booking, name='cancel-booking'),
]