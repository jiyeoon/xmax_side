"""
URL configuration for tennis_club project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from schedule.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('members/', include('members.urls')),
    path('schedule/', include('schedule.urls')),
    path('matchmaking/', include('matchmaking.urls')),
    path('board/', include('board.urls')),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
