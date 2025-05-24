"""
URL configuration for BE project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/bookings', include('apps.bookings.urls')),
    # path('api/resources', include('apps.resources.urls')),
    path('api/', include('apps.bookings.urls')),
    path('api/', include('apps.resources.urls')),
    path('api/users/', include('apps.users.urls')),   # URL cho ứng dụng quản lý người dùng
    path('api/messages/', include('apps.message.urls')),  # URL cho ứng dụng phản hồi và thông báo
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # Schema JSON
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # Swagger UI
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
