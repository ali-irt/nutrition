from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
 
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')),  # replace with your app’s URLs
    path('' , include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)