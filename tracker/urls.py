from django.contrib import admin
from django.urls import path,include
from tracker_app.urls import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',include('tracker_app.urls')),
    path('admin/', admin.site.urls),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)