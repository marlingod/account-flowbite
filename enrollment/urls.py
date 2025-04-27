# enrollment/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Admin/Teacher enrollment management
    path('course/<slug:course_slug>/students/', views.course_students, name='course_students'),
    path('course/<slug:course_slug>/enroll/', views.enroll_student, name='enroll_student'),
    path('enrollment/<int:enrollment_id>/update/', views.update_enrollment_status, name='update_enrollment_status'),
    path('enrollment/<int:enrollment_id>/unenroll/', views.unenroll_student, name='unenroll_student'),
    
    # Student views
    path('my-courses/', views.my_courses, name='my_courses'),
    path('course/<slug:course_slug>/progress/', views.view_course_progress, name='view_course_progress'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/progress/', views.mark_lesson_complete, name='mark_lesson_progress'),
    # Student enrollment views
    path('course/<slug:course_slug>/enroll/', views.enroll_in_course, name='enroll_in_course'),
       
# Admin enrollment management
    path('admin/enrollments/', views.all_enrollments, name='all_enrollments'),
    path('admin/enrollments/create/', views.create_enrollment, name='create_enrollment'),
    path('admin/enrollment/<int:enrollment_id>/delete/', views.delete_enrollment, name='delete_enrollment'),
    path('admin/stats/', views.enrollment_stats, name='enrollment_stats'),
]