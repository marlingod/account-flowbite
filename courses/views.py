# courses/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Count, Q
from django.http import HttpResponseForbidden

from accounts.decorators import teacher_required, admin_required
from .models import Category, Course, Module, Lesson, Resource
from .forms import CategoryForm, CourseForm, ModuleForm, LessonForm, ResourceForm


# Public course views
def course_list(request):
    """Display a list of published courses"""
    # Get query parameters for filtering
    category_slug = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')
    search_query = request.GET.get('q', '')
    
    # Start with published courses
    courses = Course.objects.filter(status='published')
    
    # Apply filters
    if category_slug:
        courses = courses.filter(category__slug=category_slug)
    
    if difficulty:
        courses = courses.filter(difficulty=difficulty)
    
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(learning_objectives__icontains=search_query)
        )
    
    # Get all categories for the filter sidebar
    categories = Category.objects.annotate(course_count=Count('courses'))
    
    context = {
        'courses': courses,
        'categories': categories,
        'current_category': category_slug,
        'current_difficulty': difficulty,
        'search_query': search_query,
    }
    
    return render(request, 'courses/course_list.html', context)


def course_detail(request, course_slug):
    """Display details of a specific course"""
    course = get_object_or_404(Course, slug=course_slug, status='published')
    modules = course.modules.all().prefetch_related('lessons')
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated:
        # This would come from your enrollment app
        # is_enrolled = Enrollment.objects.filter(
        #     student=request.user, 
        #     course=course, 
        #     status='active'
        # ).exists()
        pass
    
    context = {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled,
    }
    
    return render(request, 'courses/course_detail.html', context)


def category_list(request):
    """Display a list of all categories"""
    categories = Category.objects.annotate(course_count=Count('courses'))
    
    return render(request, 'courses/category_list.html', {
        'categories': categories,
    })


def category_detail(request, slug):
    """Display courses in a specific category"""
    category = get_object_or_404(Category, slug=slug)
    courses = Course.objects.filter(category=category, status='published')
    
    return render(request, 'courses/category_detail.html', {
        'category': category,
        'courses': courses,
    })


# Teacher course management views
@login_required
@teacher_required
def teacher_course_list(request):
    """Display courses taught by the current teacher"""
    courses = Course.objects.filter(instructor=request.user)
    
    return render(request, 'courses/teacher/course_list.html', {
        'courses': courses,
    })


@login_required
@teacher_required
def create_course(request):
    """Create a new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            course = form.save()
            messages.success(request, _("Course created successfully!"))
            return redirect('teacher_course_detail', course_slug=course.slug)
    else:
        form = CourseForm(user=request.user)
    
    return render(request, 'courses/teacher/create_course.html', {
        'form': form,
    }) 


@login_required
@teacher_required
def edit_course(request, course_slug):
    """Edit an existing course"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to edit this course."))
        return redirect('teacher_course_list')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Course updated successfully!"))
            return redirect('teacher_course_detail', course_slug=course.slug)
    else:
        form = CourseForm(instance=course, user=request.user)
    
    return render(request, 'courses/teacher/edit_course.html', {
        'form': form,
        'course': course,
    })


@login_required
@teacher_required
def teacher_course_detail(request, course_slug):
    """Display course details from teacher perspective"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to view this course's management page."))
        return redirect('teacher_course_list')
    
    modules = course.modules.all().prefetch_related('lessons')
    
    return render(request, 'courses/teacher/course_detail.html', {
        'course': course,
        'modules': modules,
    })

@login_required
@teacher_required
def publish_course(request, course_slug):
    """Publish a course"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to publish this course."))
        return redirect('teacher_course_list')
    
    if request.method == 'POST':
        course.status = 'published'
        course.published_at = timezone.now()
        course.save()
        messages.success(request, _("Course published successfully!"))
        return redirect('teacher_course_detail', course_slug=course.slug)
    
    return render(request, 'courses/teacher/publish_course.html', {
        'course': course,
    })



@login_required
@teacher_required
def unpublish_course(request, course_slug):
    """Unpublish a course"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to unpublish this course."))
        return redirect('teacher_course_list')
    
    if request.method == 'POST':
        course.status = 'draft'
        course.save()
        messages.success(request, _("Course unpublished and moved to drafts."))
        return redirect('teacher_course_detail', course_slug=course.slug)
    
    return render(request, 'courses/teacher/unpublish_course.html', {
        'course': course,
    })

@login_required
@teacher_required
def archive_course(request, course_slug):
    """Archive a course"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor
    if course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to archive this course."))
        return redirect('teacher_course_list')
    
    if request.method == 'POST':
        course.status = 'archived'
        course.save()
        messages.success(request, _("Course archived successfully."))
        return redirect('teacher_course_list')
    
    return render(request, 'courses/teacher/archive_course.html', {
        'course': course,
    })
    
# Module management views
@login_required
@teacher_required
def create_module(request, course_slug):
    """Create a new module for a course"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to add modules to this course."))
    
    if request.method == 'POST':
        form = ModuleForm(request.POST, course=course)
        if form.is_valid():
            module = form.save()
            messages.success(request, _("Module created successfully!"))
            return redirect('teacher_course_detail', slug=course.slug)
    else:
        # Set initial order to last module + 1
        initial_order = course.modules.count() + 1
        form = ModuleForm(course=course, initial={'order': initial_order})
    
    return render(request, 'courses/teacher/create_module.html', {
        'form': form,
        'course': course,
    })


@login_required
@teacher_required
def edit_module(request, course_slug, module_id):
    """Edit an existing module"""
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to edit this module."))
    
    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module, course=course)
        if form.is_valid():
            form.save()
            messages.success(request, _("Module updated successfully!"))
            return redirect('teacher_course_detail', slug=course.slug)
    else:
        form = ModuleForm(instance=module, course=course)
    
    return render(request, 'courses/teacher/edit_module.html', {
        'form': form,
        'course': course,
        'module': module,
    })


@login_required
@teacher_required
def delete_module(request, course_slug, module_id):
    """Delete a module"""
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to delete this module."))
    
    if request.method == 'POST':
        module.delete()
        messages.success(request, _("Module deleted successfully."))
        return redirect('teacher_course_detail', slug=course.slug)
    
    return render(request, 'courses/teacher/delete_module.html', {
        'course': course,
        'module': module,
    })


@login_required
@teacher_required
def module_detail(request, course_slug, module_id):
    """Display module details for teachers"""
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to view this module's management page."))
    
    lessons = module.lessons.all()
    
    return render(request, 'courses/teacher/module_detail.html', {
        'course': course,
        'module': module,
        'lessons': lessons,
    })


# Lesson management views
@login_required
@teacher_required
def create_lesson(request, course_slug, module_id):
    """Create a new lesson for a module"""
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to add lessons to this module."))
    
    if request.method == 'POST':
        form = LessonForm(request.POST, module=module)
        if form.is_valid():
            lesson = form.save()
            messages.success(request, _("Lesson created successfully!"))
            return redirect('module_detail', course_slug=course.slug, module_id=module.id)
    else:
        # Set initial order to last lesson + 1
        initial_order = module.lessons.count() + 1
        form = LessonForm(module=module, initial={'order': initial_order})
    
    return render(request, 'courses/teacher/create_lesson.html', {
        'form': form,
        'course': course,
        'module': module,
    })


@login_required
@teacher_required
def edit_lesson(request, course_slug, lesson_id):
    """Edit an existing lesson"""
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to edit this lesson."))
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson, module=lesson.module)
        if form.is_valid():
            form.save()
            messages.success(request, _("Lesson updated successfully!"))
            return redirect('module_detail', course_slug=course.slug, module_id=lesson.module.id)
    else:
        form = LessonForm(instance=lesson, module=lesson.module)
    
    return render(request, 'courses/teacher/edit_lesson.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
    })


@login_required
@teacher_required
def delete_lesson(request, course_slug, lesson_id):
    """Delete a lesson"""
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to delete this lesson."))
    
    if request.method == 'POST':
        module_id = lesson.module.id
        lesson.delete()
        messages.success(request, _("Lesson deleted successfully."))
        return redirect('module_detail', course_slug=course.slug, module_id=module_id)
    
    return render(request, 'courses/teacher/delete_lesson.html', {
        'course': course,
        'lesson': lesson,
    })


@login_required
@teacher_required
def lesson_detail(request, course_slug, lesson_id):
    """Display lesson details for teachers"""
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to view this lesson's management page."))
    
    resources = lesson.resources.all()
    
    return render(request, 'courses/teacher/lesson_detail.html', {
        'course': course,
        'lesson': lesson,
        'resources': resources,
    })


# Resource management views
@login_required
@teacher_required
def create_resource(request, course_slug, lesson_id):
    """Create a new resource for a lesson"""
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to add resources to this lesson."))
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, lesson=lesson)
        if form.is_valid():
            resource = form.save()
            messages.success(request, _("Resource added successfully!"))
            return redirect('lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    else:
        form = ResourceForm(lesson=lesson)
    
    return render(request, 'courses/teacher/create_resource.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
    })


@login_required
@teacher_required
def edit_resource(request, course_slug, resource_id):
    """Edit an existing resource"""
    course = get_object_or_404(Course, slug=course_slug)
    resource = get_object_or_404(Resource, id=resource_id, lesson__module__course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to edit this resource."))
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource, lesson=resource.lesson)
        if form.is_valid():
            form.save()
            messages.success(request, _("Resource updated successfully!"))
            return redirect('lesson_detail', course_slug=course.slug, lesson_id=resource.lesson.id)
    else:
        form = ResourceForm(instance=resource, lesson=resource.lesson)
    
    return render(request, 'courses/teacher/edit_resource.html', {
        'form': form,
        'course': course,
        'resource': resource,
    })


@login_required
@teacher_required
def delete_resource(request, course_slug, resource_id):
    """Delete a resource"""
    course = get_object_or_404(Course, slug=course_slug)
    resource = get_object_or_404(Resource, id=resource_id, lesson__module__course=course)
    
    # Check if user is the instructor or an admin
    if course.instructor != request.user and not request.user.is_admin_user():
        return HttpResponseForbidden(_("You don't have permission to delete this resource."))
    
    if request.method == 'POST':
        lesson_id = resource.lesson.id
        resource.delete()
        messages.success(request, _("Resource deleted successfully."))
        return redirect('lesson_detail', course_slug=course.slug, lesson_id=lesson_id)
    
    return render(request, 'courses/teacher/delete_resource.html', {
        'course': course,
        'resource': resource,
    })


# Category management (admin only)
@login_required
@admin_required
def admin_category_list(request):
    """Display a list of all categories (admin only)"""
    categories = Category.objects.annotate(course_count=Count('courses'))
    
    return render(request, 'courses/admin/category_list.html', {
        'categories': categories,
    })


@login_required
@admin_required
def create_category(request):
    """Create a new category (admin only)"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, _("Category created successfully!"))
            return redirect('admin_category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'courses/admin/create_category.html', {
        'form': form,
    })


@login_required
@admin_required
def edit_category(request, slug):
    """Edit an existing category (admin only)"""
    category = get_object_or_404(Category, slug=slug)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category updated successfully!"))
            return redirect('admin_category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'courses/admin/edit_category.html', {
        'form': form,
        'category': category,
    })


@login_required
@admin_required
def delete_category(request, slug):
    """Delete a category (admin only)"""
    category = get_object_or_404(Category, slug=slug)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, _("Category deleted successfully."))
        return redirect('admin_category_list')
    
    return render(request, 'courses/admin/delete_category.html', {
        'category': category,
    })