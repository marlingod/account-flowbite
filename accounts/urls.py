# accounts/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    # Django AllAuth URLs
    path('', include('allauth.urls')),
    
    # Profile management
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # User management (admin)
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/change-type/', views.change_user_type, name='change_user_type'),
    path('users/<int:user_id>/toggle-active/', views.toggle_user_active, name='toggle_user_active'),
]