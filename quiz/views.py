# quiz/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Avg, Count, Sum, Q
from django.forms import formset_factory

from random import sample

from accounts.decorators import student_required, teacher_required, admin_required
from courses.models import Course, Lesson, Module
from enrollment.models import Enrollment
from .models import Quiz, Question, Choice, QuizAttempt, Answer
from .forms import (
    QuizForm, QuestionForm, ChoiceForm, ChoiceFormSet, 
    MultipleChoiceAnswerForm, TrueFalseAnswerForm, ShortAnswerForm, 
    EssayAnswerForm, GradeAnswerForm
)


# Student quiz views
@login_required
@student_required
def quiz_list(request, course_slug):
    """Display all quizzes for a course"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Verify enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, _("You are not enrolled in this course."))
        return redirect('course_detail', slug=course_slug)
    
    # Get all active quizzes for this course
    quizzes = Quiz.objects.filter(course=course, is_active=True)
    
    # Get all attempts by this student for these quizzes
    attempts = QuizAttempt.objects.filter(
        student=request.user,
        quiz__in=quizzes
    ).select_related('quiz')
    
    # Create a dictionary for easy lookup
    attempt_dict = {}
    for attempt in attempts:
        if attempt.quiz_id not in attempt_dict:
            attempt_dict[attempt.quiz_id] = []
        attempt_dict[attempt.quiz_id].append(attempt)
    
    return render(request, 'quiz/quiz_list.html', {
        'course': course,
        'quizzes': quizzes,
        'attempt_dict': attempt_dict
    })


@login_required
@student_required
def start_quiz(request, course_slug, quiz_id):
    """Start a new quiz attempt"""
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, course=course, is_active=True)
    
    # Verify enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, _("You are not enrolled in this course."))
        return redirect('course_detail', slug=course_slug)
    
    # Check if there are any active attempts
    active_attempt = QuizAttempt.objects.filter(
        student=request.user,
        quiz=quiz,
        status='in_progress'
    ).first()
    
    if active_attempt:
        return redirect('continue_quiz', course_slug=course_slug, attempt_id=active_attempt.id)
    
    # Check if max attempts reached
    if quiz.max_attempts > 0:
        attempt_count = QuizAttempt.objects.filter(
            student=request.user,
            quiz=quiz,
            status__in=['completed', 'timed_out']
        ).count()
        
        if attempt_count >= quiz.max_attempts:
            messages.error(request, _("You have reached the maximum number of attempts for this quiz."))
            return redirect('quiz_list', course_slug=course_slug)
    
    # Create a new attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student=request.user,
        status='in_progress'
    )
    
    # Get all questions for this quiz
    questions = list(quiz.questions.all())
    
    # Randomize questions if needed
    if quiz.randomize_questions:
        questions = sample(questions, len(questions))
    
    # Create answers for each question
    for question in questions:
        Answer.objects.create(
            attempt=attempt,
            question=question
        )
    
    return redirect('continue_quiz', course_slug=course_slug, attempt_id=attempt.id)


@login_required
@student_required
def continue_quiz(request, course_slug, attempt_id):
    """Continue an in-progress quiz attempt"""
    course = get_object_or_404(Course, slug=course_slug)
    attempt = get_object_or_404(
        QuizAttempt, 
        id=attempt_id, 
        student=request.user, 
        status='in_progress'
    )
    quiz = attempt.quiz
    
    # Check if attempt has timed out
    if attempt.is_timed_out():
        attempt.mark_timed_out()
        messages.error(request, _("The time limit for this quiz has been reached."))
        return redirect('quiz_results', course_slug=course_slug, attempt_id=attempt.id)
    
    # Get all answers for this attempt
    answers = Answer.objects.filter(attempt=attempt).select_related('question')
    
    # Find the first unanswered question or go to the first question
    current_answer = None
    for answer in answers:
        if answer.question.question_type in ['multiple_choice', 'true_false']:
            if answer.selected_choices.count() == 0:
                current_answer = answer
                break
        elif answer.question.question_type in ['short_answer', 'essay']:
            if not answer.text_answer:
                current_answer = answer
                break
    
    # If all questions have been answered, go to the first one
    if not current_answer and answers:
        current_answer = answers.first()
    
    # Get the appropriate form for this question type
    form = None
    if current_answer:
        if current_answer.question.question_type == 'multiple_choice':
            choices = current_answer.question.choices.all()
            form = MultipleChoiceAnswerForm(
                question=current_answer.question,
                choices=choices,
                initial={
                    'selected_choices': current_answer.selected_choices.all()
                }
            )
        elif current_answer.question.question_type == 'true_false':
            choices = current_answer.question.choices.all()
            form = TrueFalseAnswerForm(
                question=current_answer.question,
                choices=choices,
                initial={
                    'selected_choice': current_answer.selected_choices.first()
                }
            )
        elif current_answer.question.question_type == 'short_answer':
            form = ShortAnswerForm(
                initial={
                    'text_answer': current_answer.text_answer
                }
            )
        elif current_answer.question.question_type == 'essay':
            form = EssayAnswerForm(
                initial={
                    'text_answer': current_answer.text_answer
                }
            )
    
    # Calculate quiz progress
    total_questions = answers.count()
    answered_count = 0
    for answer in answers:
        if answer.question.question_type in ['multiple_choice', 'true_false']:
            if answer.selected_choices.count() > 0:
                answered_count += 1
        elif answer.question.question_type in ['short_answer', 'essay']:
            if answer.text_answer:
                answered_count += 1
    
    progress_percentage = (answered_count / total_questions * 100) if total_questions > 0 else 0
    
    # Calculate time remaining if time limit exists
    time_remaining = None
    if quiz.time_limit:
        elapsed_time = timezone.now() - attempt.started_at
        time_limit = timezone.timedelta(minutes=quiz.time_limit)
        if elapsed_time < time_limit:
            time_remaining = (time_limit - elapsed_time).total_seconds()
    
    return render(request, 'quiz/take_quiz.html', {
        'course': course,
        'quiz': quiz,
        'attempt': attempt,
        'current_answer': current_answer,
        'form': form,
        'answers': answers,
        'progress_percentage': progress_percentage,
        'time_remaining': time_remaining
    })


@login_required
@student_required
def submit_answer(request, course_slug, attempt_id, answer_id):
    """Submit an answer for a question"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    course = get_object_or_404(Course, slug=course_slug)
    attempt = get_object_or_404(
        QuizAttempt, 
        id=attempt_id, 
        student=request.user, 
        status='in_progress'
    )
    answer = get_object_or_404(Answer, id=answer_id, attempt=attempt)
    
    # Check if attempt has timed out
    if attempt.is_timed_out():
        attempt.mark_timed_out()
        return JsonResponse({
            'error': 'Time limit reached',
            'redirect': f'/quiz/{course_slug}/results/{attempt.id}/'
        }, status=400)
    
    # Process the answer based on question type
    if answer.question.question_type == 'multiple_choice':
        form = MultipleChoiceAnswerForm(
            request.POST,
            question=answer.question,
            choices=answer.question.choices.all()
        )
        if form.is_valid():
            # Clear any previous selections
            answer.selected_choices.clear()
            # Add new selections
            for choice in form.cleaned_data['selected_choices']:
                answer.selected_choices.add(choice)
            # Evaluate correctness
            answer.evaluate_correctness()
            return JsonResponse({'success': True})
    
    elif answer.question.question_type == 'true_false':
        form = TrueFalseAnswerForm(
            request.POST,
            question=answer.question,
            choices=answer.question.choices.all()
        )
        if form.is_valid():
            # Clear any previous selections
            answer.selected_choices.clear()
            # Add new selection
            if form.cleaned_data['selected_choice']:
                answer.selected_choices.add(form.cleaned_data['selected_choice'])
            # Evaluate correctness
            answer.evaluate_correctness()
            return JsonResponse({'success': True})
    
    elif answer.question.question_type in ['short_answer', 'essay']:
        form = ShortAnswerForm(request.POST) if answer.question.question_type == 'short_answer' else EssayAnswerForm(request.POST)
        if form.is_valid():
            answer.text_answer = form.cleaned_data['text_answer']
            answer.save()
            return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid form data'}, status=400)


@login_required
@student_required
def submit_quiz(request, course_slug, attempt_id):
    """Submit the entire quiz"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    course = get_object_or_404(Course, slug=course_slug)
    attempt = get_object_or_404(
        QuizAttempt, 
        id=attempt_id, 
        student=request.user, 
        status='in_progress'
    )
    
    # Mark as completed and calculate results
    attempt.status = 'completed'
    attempt.save()  # This will trigger completion logic in the model
    
    return JsonResponse({
        'success': True,
        'redirect': f'/quiz/{course_slug}/results/{attempt.id}/'
    })


@login_required
@student_required
def quiz_results(request, course_slug, attempt_id):
    """Display quiz results"""
    course = get_object_or_404(Course, slug=course_slug)
    attempt = get_object_or_404(
        QuizAttempt, 
        id=attempt_id, 
        student=request.user, 
        status__in=['completed', 'timed_out']
    )
    quiz = attempt.quiz
    
    # Get all answers for this attempt
    answers = Answer.objects.filter(attempt=attempt).select_related('question')
    
    # Create a dictionary for choices
    choices_dict = {}
    for answer in answers:
        if answer.question.question_type in ['multiple_choice', 'true_false']:
            # Get all choices for this question
            choices = answer.question.choices.all()
            # Get selected choices for this answer
            selected = answer.selected_choices.all()
            # Store in dictionary
            choices_dict[answer.id] = {
                'all': choices,
                'selected': selected
            }
    
    # Check if another attempt is allowed
    can_retry = True
    if quiz.max_attempts > 0:
        attempt_count = QuizAttempt.objects.filter(
            student=request.user,
            quiz=quiz,
            status__in=['completed', 'timed_out']
        ).count()
        
        if attempt_count >= quiz.max_attempts:
            can_retry = False
    
    return render(request, 'quiz/quiz_results.html', {
        'course': course,
        'quiz': quiz,
        'attempt': attempt,
        'answers': answers,
        'choices_dict': choices_dict,
        'can_retry': can_retry,
        'show_correct': quiz.show_correct_answers
    })


# Teacher quiz management views
@login_required
@teacher_required
def teacher_quiz_list(request, course_slug):
    """Display all quizzes for a course from teacher perspective"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to view this course's quizzes."))
    
    # Get all quizzes for this course
    quizzes = Quiz.objects.filter(course=course)
    
    # Get attempt statistics for each quiz
    for quiz in quizzes:
        quiz.attempt_count = QuizAttempt.objects.filter(quiz=quiz).count()
        quiz.completion_count = QuizAttempt.objects.filter(quiz=quiz, status='completed').count()
        quiz.avg_score = QuizAttempt.objects.filter(
            quiz=quiz, 
            status='completed'
        ).aggregate(avg=Avg('percentage'))['avg'] or 0
        quiz.pass_rate = QuizAttempt.objects.filter(
            quiz=quiz, 
            status='completed', 
            passed=True
        ).count() / quiz.completion_count * 100 if quiz.completion_count > 0 else 0
    
    return render(request, 'quiz/teacher/quiz_list.html', {
        'course': course,
        'quizzes': quizzes
    })


@login_required
@teacher_required
def create_quiz(request, course_slug):
    """Create a new quiz"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to create quizzes for this course."))
    
    if request.method == 'POST':
        form = QuizForm(request.POST, course=course)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.save()
            
            messages.success(request, _("Quiz created successfully."))
            return redirect('edit_quiz', course_slug=course_slug, quiz_id=quiz.id)
    else:
        form = QuizForm(course=course)
    
    return render(request, 'quiz/teacher/create_quiz.html', {
        'course': course,
        'form': form
    })


@login_required
@teacher_required
def edit_quiz(request, course_slug, quiz_id):
    """Edit a quiz"""
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, course=course)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to edit quizzes for this course."))
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz, course=course)
        if form.is_valid():
            form.save()
            messages.success(request, _("Quiz updated successfully."))
            return redirect('teacher_quiz_list', course_slug=course_slug)
    else:
        form = QuizForm(instance=quiz, course=course)
    
    # Get questions for this quiz
    questions = quiz.questions.all().order_by('order')
    
    return render(request, 'quiz/teacher/edit_quiz.html', {
        'course': course,
        'quiz': quiz,
        'form': form,
        'questions': questions
    })


@login_required
@teacher_required
def delete_quiz(request, course_slug, quiz_id):
    """Delete a quiz"""
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, course=course)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to delete quizzes for this course."))
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, _("Quiz deleted successfully."))
        return redirect('teacher_quiz_list', course_slug=course_slug)
    
    return render(request, 'quiz/teacher/delete_quiz.html', {
        'course': course,
        'quiz': quiz
    })


@login_required
@teacher_required
def create_question(request, course_slug, quiz_id):
    """Create a new question for a quiz"""
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, course=course)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to create questions for this quiz."))
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.order = quiz.questions.count() + 1  # Set order to last
            question.save()
            
            # For multiple choice and true/false, redirect to add choices
            if question.question_type in ['multiple_choice', 'true_false']:
                return redirect('edit_choices', course_slug=course_slug, question_id=question.id)
            
            messages.success(request, _("Question created successfully."))
            return redirect('edit_quiz', course_slug=course_slug, quiz_id=quiz.id)
    else:
        form = QuestionForm()
    
    return render(request, 'quiz/teacher/create_question.html', {
        'course': course,
        'quiz': quiz,
        'form': form
    })


@login_required
@teacher_required
def edit_question(request, course_slug, question_id):
    """Edit a question"""
    course = get_object_or_404(Course, slug=course_slug)
    question = get_object_or_404(Question, id=question_id, quiz__course=course)
    quiz = question.quiz
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to edit questions for this quiz."))
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save()
            
            messages.success(request, _("Question updated successfully."))
            return redirect('edit_quiz', course_slug=course_slug, quiz_id=quiz.id)
    else:
        form = QuestionForm(instance=question)
    
    return render(request, 'quiz/teacher/edit_question.html', {
        'course': course,
        'quiz': quiz,
        'question': question,
        'form': form
    })


@login_required
@teacher_required
def delete_question(request, course_slug, question_id):
    """Delete a question"""
    course = get_object_or_404(Course, slug=course_slug)
    question = get_object_or_404(Question, id=question_id, quiz__course=course)
    quiz = question.quiz
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to delete questions for this quiz."))
    
    if request.method == 'POST':
        # Delete the question
        question.delete()
        
        # Reorder remaining questions
        for i, q in enumerate(quiz.questions.all().order_by('order')):
            q.order = i + 1
            q.save()
        
        messages.success(request, _("Question deleted successfully."))
        return redirect('edit_quiz', course_slug=course_slug, quiz_id=quiz.id)
    
    return render(request, 'quiz/teacher/delete_question.html', {
        'course': course,
        'quiz': quiz,
        'question': question
    })


@login_required
@teacher_required
def edit_choices(request, course_slug, question_id):
    """Edit choices for a multiple choice or true/false question"""
    course = get_object_or_404(Course, slug=course_slug)
    question = get_object_or_404(Question, id=question_id, quiz__course=course)
    quiz = question.quiz
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to edit choices for this question."))
    
    # Make sure this is a question type that has choices
    if question.question_type not in ['multiple_choice', 'true_false']:
        messages.error(request, _("This question type does not have choices."))
        return redirect('edit_quiz', course_slug=course_slug, quiz_id=quiz.id)
    
    # For true/false, ensure there are exactly two choices (if none exist yet)
    if question.question_type == 'true_false' and question.choices.count() == 0:
        # Create True and False choices
        Choice.objects.create(
            question=question,
            text=_("True"),
            is_correct=True,  # Default to True being correct
            order=1
        )
        Choice.objects.create(
            question=question,
            text=_("False"),
            is_correct=False,
            order=2
        )
    
    if request.method == 'POST':
        formset = ChoiceFormSet(request.POST, instance=question)
        if formset.is_valid():
            formset.save()
            
            # For true/false, ensure only one choice is marked as correct
            if question.question_type == 'true_false':
                choices = question.choices.all()
                if choices.filter(is_correct=True).count() != 1:
                    first_choice = choices.first()
                    if first_choice:
                        first_choice.is_correct = True
                        first_choice.save()
                        
                        for choice in choices.exclude(id=first_choice.id):
                            choice.is_correct = False
                            choice.save()
            
            messages.success(request, _("Choices updated successfully."))
            return redirect('edit_quiz', course_slug=course_slug, quiz_id=quiz.id)
    else:
        formset = ChoiceFormSet(instance=question)
    
    return render(request, 'quiz/teacher/edit_choices.html', {
        'course': course,
        'quiz': quiz,
        'question': question,
        'formset': formset
    })


@login_required
@teacher_required
def quiz_attempts(request, course_slug, quiz_id):
    """View all attempts for a quiz"""
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, course=course)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to view attempts for this quiz."))
    
    # Get all attempts for this quiz
    attempts = QuizAttempt.objects.filter(quiz=quiz).select_related('student')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        attempts = attempts.filter(status=status_filter)
    
    # Filter by passed if provided
    passed_filter = request.GET.get('passed', '')
    if passed_filter:
        if passed_filter == 'yes':
            attempts = attempts.filter(passed=True)
        elif passed_filter == 'no':
            attempts = attempts.filter(Q(passed=False) | Q(passed=None))
    
    # Filter by search query if provided
    search_query = request.GET.get('q', '')
    if search_query:
        attempts = attempts.filter(
            Q(student__username__icontains=search_query) |
            Q(student__email__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )
    
    return render(request, 'quiz/teacher/quiz_attempts.html', {
        'course': course,
        'quiz': quiz,
        'attempts': attempts,
        'status_filter': status_filter,
        'passed_filter': passed_filter,
        'search_query': search_query
    })


@login_required
@teacher_required
def grade_essay(request, course_slug, answer_id):
    """Grade an essay or short answer question"""
    course = get_object_or_404(Course, slug=course_slug)
    answer = get_object_or_404(Answer, id=answer_id, attempt__quiz__course=course)
    quiz = answer.attempt.quiz
    question = answer.question
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to grade answers for this quiz."))
    
    # Make sure this is a question type that needs manual grading
    if question.question_type not in ['short_answer', 'essay']:
        messages.error(request, _("This question type does not need manual grading."))
        return redirect('quiz_attempts', course_slug=course_slug, quiz_id=quiz.id)
    
    if request.method == 'POST':
        form = GradeAnswerForm(request.POST, instance=answer)
        if form.is_valid():
            answer = form.save(commit=False)
            # Store points earned
            answer.points_earned = form.cleaned_data['points_earned']
            answer.is_correct = form.cleaned_data['is_correct']
            answer.feedback = form.cleaned_data['feedback']
            answer.save()
            
            # Update attempt score
            attempt = answer.attempt
            if attempt.status == 'completed':
                total_points = attempt.quiz.get_total_points()
                if total_points > 0:
                    attempt.score = sum(a.points_earned for a in attempt.answers.all())
                    attempt.percentage = (attempt.score / total_points) * 100
                    attempt.passed = attempt.percentage >= attempt.quiz.passing_score
                    attempt.save()
            
            messages.success(request, _("Answer graded successfully."))
            return redirect('view_attempt', course_slug=course_slug, attempt_id=answer.attempt.id)
    else:
        form = GradeAnswerForm(instance=answer)
    
    return render(request, 'quiz/teacher/grade_essay.html', {
        'course': course,
        'quiz': quiz,
        'answer': answer,
        'form': form
    })


@login_required
@teacher_required
def view_attempt(request, course_slug, attempt_id):
    """View a specific quiz attempt"""
    course = get_object_or_404(Course, slug=course_slug)
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, quiz__course=course)
    quiz = attempt.quiz
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to view attempts for this quiz."))
    
    # Get all answers for this attempt
    answers = Answer.objects.filter(attempt=attempt).select_related('question')
    
    # Create a dictionary for choices
    choices_dict = {}
    for answer in answers:
        if answer.question.question_type in ['multiple_choice', 'true_false']:
            # Get all choices for this question
            choices = answer.question.choices.all()
            # Get selected choices for this answer
            selected = answer.selected_choices.all()
            # Store in dictionary
            choices_dict[answer.id] = {
                'all': choices,
                'selected': selected
            }
    
    return render(request, 'quiz/teacher/view_attempt.html', {
        'course': course,
        'quiz': quiz,
        'attempt': attempt,
        'answers': answers,
        'choices_dict': choices_dict
    })


# Analytics views for quizzes
@login_required
@teacher_required
def quiz_analytics(request, course_slug, quiz_id):
    """View analytics for a specific quiz"""
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, course=course)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to view analytics for this quiz."))
    
    # Get statistics for the quiz
    stats = {
        'total_attempts': QuizAttempt.objects.filter(quiz=quiz).count(),
        'completed_attempts': QuizAttempt.objects.filter(quiz=quiz, status='completed').count(),
        'timed_out_attempts': QuizAttempt.objects.filter(quiz=quiz, status='timed_out').count(),
        'average_score': QuizAttempt.objects.filter(
            quiz=quiz, 
            status='completed'
        ).aggregate(avg=Avg('percentage'))['avg'] or 0,
        'pass_rate': QuizAttempt.objects.filter(
            quiz=quiz, 
            status='completed', 
            passed=True
        ).count() / QuizAttempt.objects.filter(
            quiz=quiz, 
            status='completed'
        ).count() * 100 if QuizAttempt.objects.filter(quiz=quiz, status='completed').count() > 0 else 0,
        'average_time': QuizAttempt.objects.filter(
            quiz=quiz, 
            status='completed', 
            time_spent__isnull=False
        ).aggregate(avg=Avg('time_spent'))['avg'],
    }
    
    # Get question-level statistics
    questions = []
    for question in quiz.questions.all():
        correct_count = Answer.objects.filter(
            question=question,
            is_correct=True,
            attempt__status='completed'
        ).count()
        
        total_count = Answer.objects.filter(
            question=question,
            attempt__status='completed'
        ).count()
        
        success_rate = (correct_count / total_count * 100) if total_count > 0 else 0
        
        questions.append({
            'question': question,
            'success_rate': success_rate,
            'correct_count': correct_count,
            'total_count': total_count
        })
    
    # Get score distribution
    score_distribution = {}
    ranges = ['0-20', '21-40', '41-60', '61-80', '81-100']
    
    for r in ranges:
        min_score, max_score = map(int, r.split('-'))
        count = QuizAttempt.objects.filter(
            quiz=quiz,
            status='completed',
            percentage__gte=min_score,
            percentage__lte=max_score
        ).count()
        
        score_distribution[r] = count
    
    return render(request, 'quiz/teacher/quiz_analytics.html', {
        'course': course,
        'quiz': quiz,
        'stats': stats,
        'questions': questions,
        'score_distribution': score_distribution
    })