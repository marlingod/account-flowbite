# courses/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public course views
    path('', views.course_list, name='course_list'),
    path('course/<slug:course_slug>/', views.course_detail, name='course_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:course_slug>/', views.category_detail, name='category_detail'),
    
    # Teacher views
    path('teacher/courses/', views.teacher_course_list, name='teacher_course_list'),
    path('teacher/course/create/', views.create_course, name='create_course'),
    path('teacher/course/<slug:course_slug>/', views.teacher_course_detail, name='teacher_course_detail'),
    path('teacher/course/<slug:course_slug>/edit/', views.edit_course, name='edit_course'),
    path('teacher/course/<slug:course_slug>/publish/', views.publish_course, name='publish_course'),
    path('teacher/course/<slug:course_slug>/unpublish/', views.unpublish_course, name='unpublish_course'),
    path('teacher/course/<slug:course_slug>/archive/', views.archive_course, name='archive_course'),
    
    # Module management
    path('teacher/course/<slug:course_slug>/module/create/', views.create_module, name='create_module'),
    path('teacher/course/<slug:course_slug>/module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('teacher/course/<slug:course_slug>/module/<int:module_id>/edit/', views.edit_module, name='edit_module'),
    path('teacher/course/<slug:course_slug>/module/<int:module_id>/delete/', views.delete_module, name='delete_module'),
    
    path('teacher/course/<slug:course_slug>/unpublish/', views.unpublish_course, name='unpublish_course'),
    
    # Lesson management
    path('teacher/course/<slug:course_slug>/module/<int:module_id>/lesson/create/', views.create_lesson, name='create_lesson'),
    path('teacher/course/<slug:course_slug>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('teacher/course/<slug:course_slug>/lesson/<int:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('teacher/course/<slug:course_slug>/lesson/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    
    # Resource management
    path('teacher/course/<slug:course_slug>/lesson/<int:lesson_id>/resource/create/', views.create_resource, name='create_resource'),
    path('teacher/course/<slug:course_slug>/resource/<int:resource_id>/edit/', views.edit_resource, name='edit_resource'),
    path('teacher/course/<slug:course_slug>/resource/<int:resource_id>/delete/', views.delete_resource, name='delete_resource'),
    
    # Category management (admin only)
    path('admin/categories/', views.admin_category_list, name='admin_category_list'),
    path('admin/category/create/', views.create_category, name='create_category'),
    path('admin/category/<slug:course_slug>/edit/', views.edit_category, name='edit_category'),
    path('admin/category/<slug:course_slug>/delete/', views.delete_category, name='delete_category'),
]