# enrollment/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Q

from accounts.decorators import student_required, teacher_required, admin_required
from courses.models import Course, Lesson
from .models import Enrollment, LessonProgress
from .forms import EnrollmentForm


@login_required
@student_required
def enroll_course(request, course_slug):
    """Student enrolls in a course"""
    course = get_object_or_404(Course, slug=course_slug, status='published')
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.warning(request, _("You are already enrolled in this course."))
        return redirect('course_detail', slug=course_slug)
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            # Create enrollment
            enrollment = Enrollment.objects.create(
                student=request.user,
                course=course,
                status='active'
            )
            
            # Create lesson progress objects for all lessons
            lessons = Lesson.objects.filter(module__course=course)
            lesson_progress_objects = []
            for lesson in lessons:
                lesson_progress_objects.append(
                    LessonProgress(
                        enrollment=enrollment,
                        lesson=lesson
                    )
                )
            
            # Bulk create all lesson progress objects
            LessonProgress.objects.bulk_create(lesson_progress_objects)
            
            messages.success(request, _("You have successfully enrolled in this course."))
            return redirect('student_course_detail', slug=course_slug)
    else:
        form = EnrollmentForm()
    
    return render(request, 'enrollment/enroll_course.html', {
        'course': course,
        'form': form
    })


@login_required
@student_required
def student_dashboard(request):
    """Display student dashboard with enrollments"""
    # Get active enrollments
    active_enrollments = Enrollment.objects.filter(
        student=request.user,
        status='active'
    ).select_related('course').order_by('-enrolled_at')
    
    # Get completed courses
    completed_enrollments = Enrollment.objects.filter(
        student=request.user,
        status='completed'
    ).select_related('course').order_by('-completion_date')
    
    # Get course recommendations (courses the student isn't enrolled in)
    recommended_courses = Course.objects.filter(
        status='published'
    ).exclude(
        enrollments__student=request.user
    ).order_by('-created_at')[:5]
    
    return render(request, 'enrollment/student_dashboard.html', {
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'recommended_courses': recommended_courses
    })


@login_required
@student_required
def student_course_detail(request, slug):
    """Display course details for enrolled student"""
    course = get_object_or_404(Course, slug=slug)
    
    # Verify enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, _("You are not enrolled in this course."))
        return redirect('course_detail', slug=slug)
    
    # Get modules with their lessons
    modules = course.modules.all().prefetch_related('lessons')
    
    # Get lesson progress for this enrollment
    lesson_progress = LessonProgress.objects.filter(
        enrollment=enrollment
    ).select_related('lesson')
    
    # Create a dictionary for quick lookup of lesson progress
    progress_dict = {lp.lesson_id: lp for lp in lesson_progress}
    
    return render(request, 'enrollment/student_course_detail.html', {
        'course': course,
        'enrollment': enrollment,
        'modules': modules,
        'progress_dict': progress_dict
    })


@login_required
@student_required
def view_lesson(request, course_slug, lesson_id):
    """View a lesson as an enrolled student"""
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    
    # Verify enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, _("You are not enrolled in this course."))
        return redirect('course_detail', slug=course_slug)
    
    # Get or create lesson progress
    lesson_progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    # Mark as in progress if not completed
    if lesson_progress.status != 'completed':
        lesson_progress.mark_as_started()
    
    # Get next and previous lessons for navigation
    try:
        next_lesson = Lesson.objects.filter(
            module__course=course,
            module__order__gte=lesson.module.order,
            order__gt=lesson.order if lesson.module.order == lesson.module.order else 0
        ).order_by('module__order', 'order').first()
    except Lesson.DoesNotExist:
        next_lesson = None
    
    try:
        prev_lesson = Lesson.objects.filter(
            module__course=course,
            module__order__lte=lesson.module.order,
            order__lt=lesson.order if lesson.module.order == lesson.module.order else float('inf')
        ).order_by('-module__order', '-order').first()
    except Lesson.DoesNotExist:
        prev_lesson = None
    
    return render(request, 'enrollment/view_lesson.html', {
        'course': course,
        'lesson': lesson,
        'lesson_progress': lesson_progress,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson
    })


@login_required
@student_required
def complete_lesson(request, course_slug, lesson_id):
    """Mark a lesson as completed"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    
    # Verify enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        return JsonResponse({'error': 'Not enrolled in this course'}, status=403)
    
    # Get or create lesson progress
    lesson_progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    # Mark as completed
    lesson_progress.mark_as_completed()
    
    # Return updated enrollment progress
    return JsonResponse({
        'success': True,
        'progress': enrollment.progress,
        'status': lesson_progress.status,
        'completed_at': lesson_progress.completed_at.isoformat() if lesson_progress.completed_at else None
    })


@login_required
@teacher_required
def course_students(request, course_slug):
    """View students enrolled in a course (teacher only)"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to view this course's students."))
    
    # Get enrollments for this course
    enrollments = Enrollment.objects.filter(
        course=course
    ).select_related('student').order_by('student__last_name', 'student__first_name')
    
    return render(request, 'enrollment/course_students.html', {
        'course': course,
        'enrollments': enrollments
    })


@login_required
@teacher_required
def student_progress(request, course_slug, student_id):
    """View a specific student's progress in a course (teacher only)"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to view this student's progress."))
    
    # Get student and enrollment
    student = get_object_or_404(User, id=student_id)
    enrollment = get_object_or_404(Enrollment, course=course, student=student)
    
    # Get lesson progress
    lesson_progress = LessonProgress.objects.filter(
        enrollment=enrollment
    ).select_related('lesson').order_by('lesson__module__order', 'lesson__order')
    
    return render(request, 'enrollment/student_progress.html', {
        'course': course,
        'student': student,
        'enrollment': enrollment,
        'lesson_progress': lesson_progress
    })


@login_required
@admin_required
def enrollment_stats(request):
    """View enrollment statistics (admin only)"""
    # Overall statistics
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(status='active').count()
    completed_enrollments = Enrollment.objects.filter(status='completed').count()
    dropped_enrollments = Enrollment.objects.filter(status='dropped').count()
    
    # Course statistics
    courses = Course.objects.annotate(
        enrollment_count=Count('enrollments'),
        active_count=Count('enrollments', filter=Q(enrollments__status='active')),
        completed_count=Count('enrollments', filter=Q(enrollments__status='completed')),
        dropped_count=Count('enrollments', filter=Q(enrollments__status='dropped'))
    ).order_by('-enrollment_count')
    
    # Monthly enrollment trends (last 12 months)
    current_month = timezone.now().date().replace(day=1)
    months = []
    monthly_counts = []
    
    for i in range(12):
        month_start = current_month.replace(month=((current_month.month - i - 1) % 12) + 1)
        if month_start.month > current_month.month:
            month_start = month_start.replace(year=current_month.year - 1)
        
        month_end = month_start.replace(month=month_start.month % 12 + 1)
        if month_end.month < month_start.month:
            month_end = month_end.replace(year=month_start.year + 1)
        
        count = Enrollment.objects.filter(
            enrolled_at__gte=month_start,
            enrolled_at__lt=month_end
        ).count()
        
        months.insert(0, month_start.strftime('%b %Y'))
        monthly_counts.insert(0, count)
    
    return render(request, 'enrollment/enrollment_stats.html', {
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'dropped_enrollments': dropped_enrollments,
        'courses': courses,
        'months': months,
        'monthly_counts': monthly_counts
    })