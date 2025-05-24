from rest_framework import permissions
from .models import Booking

class IsStudentOrTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['student', 'teacher']

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'

class IsBookingOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class CanCancelBooking(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.status == 'CONFIRMED'

class IsManagerForStudySpace(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        return request.user.is_authenticated and request.user.role == 'manager'