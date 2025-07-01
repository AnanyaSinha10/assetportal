# assetportal/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('baseapp.urls')), # Includes all URLs from your baseapp
]

# ONLY add this in development (when DEBUG is True)
# In production, web servers (like Nginx, Apache) handle serving media files directly.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)