from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
    path('', views.schedule_calendar, name='calendar'),
    path('api/events/', views.events_api, name='events_api'),
    path('api/event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('api/event/create/', views.event_create, name='event_create'),
    path('api/event/update/<int:event_id>/', views.event_update, name='event_update'),
    path('api/event/delete/<int:event_id>/', views.event_delete, name='event_delete'),
]

