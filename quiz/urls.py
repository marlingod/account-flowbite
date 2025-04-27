# quiz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Student views
    path('<slug:course_slug>/quizzes/', views.quiz_list, name='quiz_list'),
    path('<slug:course_slug>/quiz/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('<slug:course_slug>/continue/<int:attempt_id>/', views.continue_quiz, name='continue_quiz'),
    path('<slug:course_slug>/submit-answer/<int:attempt_id>/<int:answer_id>/', views.submit_answer, name='submit_answer'),
    path('<slug:course_slug>/submit-quiz/<int:attempt_id>/', views.submit_quiz, name='submit_quiz'),
    path('<slug:course_slug>/results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    
    # Teacher views
    path('<slug:course_slug>/teacher/quizzes/', views.teacher_quiz_list, name='teacher_quiz_list'),
    path('<slug:course_slug>/teacher/quiz/create/', views.create_quiz, name='create_quiz'),
    path('<slug:course_slug>/teacher/quiz/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('<slug:course_slug>/teacher/quiz/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('<slug:course_slug>/teacher/quiz/<int:quiz_id>/question/create/', views.create_question, name='create_question'),
    path('<slug:course_slug>/teacher/question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('<slug:course_slug>/teacher/question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('<slug:course_slug>/teacher/question/<int:question_id>/choices/', views.edit_choices, name='edit_choices'),
    
    # Attempt management
    path('<slug:course_slug>/teacher/quiz/<int:quiz_id>/attempts/', views.quiz_attempts, name='quiz_attempts'),
    path('<slug:course_slug>/teacher/attempt/<int:attempt_id>/', views.view_attempt, name='view_attempt'),
    path('<slug:course_slug>/teacher/grade/<int:answer_id>/', views.grade_essay, name='grade_essay'),
    
    # Analytics
    path('<slug:course_slug>/teacher/quiz/<int:quiz_id>/analytics/', views.quiz_analytics, name='quiz_analytics'),
]