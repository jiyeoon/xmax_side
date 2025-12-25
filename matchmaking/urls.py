from django.urls import path
from . import views

app_name = 'matchmaking'

urlpatterns = [
    path('', views.matchmaking_page, name='page'),
    path('api/generate/', views.generate_matches, name='generate'),
    path('api/regenerate/', views.regenerate_matches, name='regenerate'),
    path('api/session/<int:session_id>/', views.session_detail, name='session_detail'),
]

