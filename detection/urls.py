from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('detect/', views.detect_disease, name='detect_disease'),
    path('detect-live/', views.detect_live_proxy, name='detect_live'),
    path('detect-upload/', views.detect_upload_proxy, name='detect_upload'),
    path('history/', views.detection_history, name='detection_history'),
    path('user/', views.user_info, name='user_info'),
] 