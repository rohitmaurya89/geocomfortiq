from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('analyze/', views.analyze, name='analyze'),
    path('dashboard/<int:result_id>/', views.dashboard_detail, name='dashboard_detail'),
    path('api/cities/', views.api_cities, name='api_cities'),
    path('api/localities/', views.api_localities, name='api_localities'),
    path('api/result/<int:result_id>/json/', views.api_result_json, name='api_result_json'),
]
