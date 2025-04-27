
### from urls 
urlpatterns = [
    # Student views
    path('dashboard/', views_old.student_dashboard, name='student_dashboard'),
    path('course/<slug:slug>/', views_old.student_course_detail, name='student_course_detail'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/', views_old.view_lesson, name='view_lesson'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/complete/', views_old.complete_lesson, name='complete_lesson'),
    path('enroll/<slug:course_slug>/', views_old.enroll_course, name='enroll_course'),
    
    # Teacher views
    path('course/<slug:course_slug>/students/', views_old.course_students, name='course_students'),
    path('course/<slug:course_slug>/student/<int:student_id>/progress/', views_old.student_progress, name='student_progress'),
    
    # Admin views
    path('stats/', views_old.enrollment_stats, name='enrollment_stats'),
]

