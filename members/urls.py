from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('', views.member_list, name='list'),
    path('api/list/', views.member_api_list, name='api_list'),
    path('api/detail/<int:member_id>/', views.member_detail, name='detail'),
    path('api/create/', views.member_create, name='create'),
    path('api/update/<int:member_id>/', views.member_update, name='update'),
    path('api/delete/<int:member_id>/', views.member_delete, name='delete'),
]

