"""
URL configuration for tennis_club project.
"""
from django.contrib import admin
from django.urls import path, include
from schedule.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('members/', include('members.urls')),
    path('schedule/', include('schedule.urls')),
    path('matchmaking/', include('matchmaking.urls')),
]

