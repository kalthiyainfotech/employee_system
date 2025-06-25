from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('tracker/', tracker, name='tracker'),
    path('', login_view, name='login_view'),
    path('logout/', logout_view, name='logout_view'),
    

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
