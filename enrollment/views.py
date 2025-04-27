# enrollment/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, Q
from django.urls import reverse

from accounts.decorators import student_required, teacher_required, admin_required
from accounts.models import User
from courses.models import Course, Module, Lesson
from .models import Enrollment, LessonProgress
from .forms import EnrollmentForm, EnrollmentStatusForm

# Admin/Teacher enrollment management views
@login_required
def enroll_student(request, course_slug):
    """Enroll a student in a course - restricted to admins and teachers"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is admin or the course instructor
    if not (request.user.is_admin_user() or (request.user.is_teacher() and course.instructor == request.user)):
        messages.error(request, _("You don't have permission to enroll students in this course."))
        return redirect('course_detail', slug=course_slug)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        student = get_object_or_404(User, id=student_id)
        
        # Check if student is already enrolled
        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.warning(request, _("This student is already enrolled in this course."))
            return redirect('course_students', course_slug=course_slug)
        
        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=student,
            course=course,
            status='active'
        )
        
        # Create lesson progress records for each lesson
        lessons = Lesson.objects.filter(module__course=course)
        for lesson in lessons:
            LessonProgress.objects.create(
                enrollment=enrollment,
                lesson=lesson,
                status='not_started'
            )
        
        messages.success(request, _("Student successfully enrolled in the course."))
        return redirect('course_students', course_slug=course_slug)
    
    # Get students who are not enrolled yet
    enrolled_student_ids = Enrollment.objects.filter(course=course).values_list('student_id', flat=True)
    available_students = User.objects.filter(user_type='student').exclude(id__in=enrolled_student_ids)
    
    return render(request, 'enrollment/enroll_student.html', {
        'course': course,
        'available_students': available_students
    })

@login_required
def course_students(request, course_slug):
    """View students enrolled in a course - restricted to admins and teachers"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is admin or the course instructor
    if not (request.user.is_admin_user() or (request.user.is_teacher() and course.instructor == request.user)):
        messages.error(request, _("You don't have permission to view the students in this course."))
        return redirect('course_detail', slug=course_slug)
    
    # Get enrollments
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    # Search by student name/email if provided
    search_query = request.GET.get('q', '')
    if search_query:
        enrollments = enrollments.filter(
            Q(student__username__icontains=search_query) |
            Q(student__email__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )
    
    return render(request, 'enrollment/course_students.html', {
        'course': course,
        'enrollments': enrollments,
        'status_filter': status_filter,
        'search_query': search_query
    })

@login_required
def update_enrollment_status(request, enrollment_id):
    """Update a student's enrollment status - restricted to admins and teachers"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    course = enrollment.course
    
    # Check if user is admin or the course instructor
    if not (request.user.is_admin_user() or (request.user.is_teacher() and course.instructor == request.user)):
        messages.error(request, _("You don't have permission to update enrollment status."))
        return redirect('course_detail', slug=course.slug)
    
    if request.method == 'POST':
        form = EnrollmentStatusForm(request.POST, instance=enrollment)
        if form.is_valid():
            enrollment = form.save(commit=False)
            
            # If marking as completed, set completion date
            if enrollment.status == 'completed' and not enrollment.completion_date:
                enrollment.completion_date = timezone.now()
                enrollment.progress = 100
            
            enrollment.save()
            
            messages.success(request, _("Enrollment status updated successfully."))
            return redirect('course_students', course_slug=course.slug)
    else:
        form = EnrollmentStatusForm(instance=enrollment)
    
    return render(request, 'enrollment/update_enrollment_status.html', {
        'form': form,
        'enrollment': enrollment,
        'course': course
    })

@login_required
def unenroll_student(request, enrollment_id):
    """Unenroll a student from a course - restricted to admins and teachers"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    course = enrollment.course
    
    # Check if user is admin or the course instructor
    if not (request.user.is_admin_user() or (request.user.is_teacher() and course.instructor == request.user)):
        messages.error(request, _("You don't have permission to unenroll students from this course."))
        return redirect('course_detail', slug=course.slug)
    
    if request.method == 'POST':
        # Delete lesson progress first (to maintain referential integrity)
        LessonProgress.objects.filter(enrollment=enrollment).delete()
        
        # Delete the enrollment
        student_name = f"{enrollment.student.first_name} {enrollment.student.last_name}".strip()
        if not student_name:
            student_name = enrollment.student.username
            
        enrollment.delete()
        
        messages.success(request, _("Student {} has been unenrolled from the course.").format(student_name))
        return redirect('course_students', course_slug=course.slug)
    
    return render(request, 'enrollment/unenroll_student.html', {
        'enrollment': enrollment,
        'course': course
    })

# Student enrollment views (now just for viewing their enrollments)
@login_required
@student_required
def my_courses(request):
    """View student's enrolled courses"""
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    # Search by title if provided
    search_query = request.GET.get('q', '')
    if search_query:
        enrollments = enrollments.filter(
            Q(course__title__icontains=search_query) |
            Q(course__description__icontains=search_query)
        )
    
    return render(request, 'enrollment/my_courses.html', {
        'enrollments': enrollments,
        'status_filter': status_filter,
        'search_query': search_query
    })

@login_required
@student_required
def view_course_progress(request, course_slug):
    """View progress in a specific course"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if enrolled
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, _("You are not enrolled in this course."))
        return redirect('course_detail', slug=course_slug)
    
    # Get lesson progress
    lesson_progress = LessonProgress.objects.filter(
        enrollment=enrollment
    ).select_related('lesson', 'lesson__module')
    
    # Organize by module
    modules = Module.objects.filter(course=course).prefetch_related('lessons')
    module_progress = {}
    
    for module in modules:
        module_lessons = module.lessons.all()
        completed_lessons = sum(1 for lp in lesson_progress if lp.lesson.module_id == module.id and lp.status == 'completed')
        total_lessons = module_lessons.count()
        
        if total_lessons > 0:
            completion_percentage = int((completed_lessons / total_lessons) * 100)
        else:
            completion_percentage = 0
            
        module_progress[module.id] = {
            'module': module,
            'completed': completed_lessons,
            'total': total_lessons,
            'percentage': completion_percentage,
            'lessons': {lesson.id: 'not_started' for lesson in module_lessons}
        }
    
    # Update with actual progress status
    for progress in lesson_progress:
        if progress.lesson.module_id in module_progress:
            module_progress[progress.lesson.module_id]['lessons'][progress.lesson_id] = progress.status
    
    return render(request, 'enrollment/course_progress.html', {
        'course': course,
        'enrollment': enrollment,
        'module_progress': module_progress
    })

@login_required
@student_required
def mark_lesson_complete(request, course_slug, lesson_id):
    """Mark a lesson as completed (AJAX endpoint)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    
    # Get enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        return JsonResponse({'error': 'You are not enrolled in this course'}, status=403)
    
    # Get or create lesson progress
    lesson_progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    # Update status based on the request
    status = request.POST.get('status')
    if status in ['not_started', 'in_progress', 'completed']:
        lesson_progress.status = status
        if status == 'in_progress':
            lesson_progress.last_accessed = timezone.now()
        elif status == 'completed':
            lesson_progress.completed_at = timezone.now()
        
        lesson_progress.save()
        
        # Update enrollment progress
        lesson_progress.update_enrollment_progress()
        
        return JsonResponse({
            'success': True,
            'status': status,
            'progress': enrollment.progress
        })
    
    return JsonResponse({'error': 'Invalid status value'}, status=400)


@login_required
@admin_required
def enrollment_stats(request):
    """View enrollment statistics (admin view)"""
    # Get overall statistics
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(status='active').count()
    completed_enrollments = Enrollment.objects.filter(status='completed').count()
    
    # Get course statistics
    course_stats = Course.objects.annotate(
        total_enrolled=Count('enrollments'),
        active_enrolled=Count('enrollments', filter=Q(enrollments__status='active')),
        completion_rate=Count('enrollments', filter=Q(enrollments__status='completed')) * 100.0 / Count('enrollments'),
    ).filter(total_enrolled__gt=0)
    
    # Get monthly enrollment data for the chart
    from django.db.models.functions import TruncMonth
    
    monthly_data = Enrollment.objects.annotate(
        month=TruncMonth('enrolled_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    return render(request, 'enrollment/admin/enrollment_stats.html', {
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'course_stats': course_stats,
        'monthly_data': monthly_data,
    })

@login_required
@admin_required
def all_enrollments(request):
    """View all enrollments across all courses (admin view)"""
    # Get all enrollments
    enrollments = Enrollment.objects.all().select_related('student', 'course')
    
    # Filter by course if provided
    course_filter = request.GET.get('course', '')
    if course_filter:
        enrollments = enrollments.filter(course__id=course_filter)
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    # Filter by search query if provided
    search_query = request.GET.get('q', '')
    if search_query:
        enrollments = enrollments.filter(
            Q(student__username__icontains=search_query) |
            Q(student__email__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(course__title__icontains=search_query)
        )
    
    # Get all courses for filter dropdown
    courses = Course.objects.all()
    
    return render(request, 'enrollment/admin/all_enrollments.html', {
        'enrollments': enrollments,
        'courses': courses,
        'course_filter': course_filter,
        'status_filter': status_filter,
        'search_query': search_query
    })

@login_required
@admin_required
def create_enrollment(request):
    """Create a new enrollment (admin view)"""
    if request.method == 'POST':
        student_id = request.POST.get('student')
        course_id = request.POST.get('course')
        status = request.POST.get('status', 'active')
        
        try:
            student = User.objects.get(id=student_id)
            course = Course.objects.get(id=course_id)
            
            # Check if enrollment already exists
            if Enrollment.objects.filter(student=student, course=course).exists():
                messages.error(request, _("This student is already enrolled in the course."))
                return redirect('all_enrollments')
            
            # Create enrollment
            enrollment = Enrollment.objects.create(
                student=student,
                course=course,
                status=status
            )
            
            # Create lesson completion records for all lessons
            for module in course.modules.all():
                for lesson in module.lessons.all():
                    LessonCompletion.objects.create(
                        enrollment=enrollment,
                        lesson=lesson
                    )
            
            messages.success(request, _("Enrollment created successfully."))
            return redirect('enrollment_detail', enrollment_id=enrollment.id)
        
        except (User.DoesNotExist, Course.DoesNotExist):
            messages.error(request, _("Invalid student or course."))
    
    # Get all students and courses for the form
    students = User.objects.filter(user_type='student')
    courses = Course.objects.all()
    
    return render(request, 'enrollment/admin/create_enrollment.html', {
        'students': students,
        'courses': courses
    })

@login_required
@admin_required
def delete_enrollment(request, enrollment_id):
    """Delete an enrollment (admin view)"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    if request.method == 'POST':
        # Delete all lesson completions
        LessonCompletion.objects.filter(enrollment=enrollment).delete()
        
        # Delete the enrollment
        enrollment.delete()
        
        messages.success(request, _("Enrollment deleted successfully."))
        return redirect('all_enrollments')
    
    return render(request, 'enrollment/admin/delete_enrollment.html', {
        'enrollment': enrollment
    })