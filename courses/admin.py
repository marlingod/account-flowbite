# courses/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Category, Course, Module, Lesson, Resource


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 0
    fields = ('title', 'content_type', 'content', 'video_url', 'duration', 'order', 'is_required')


class ModuleInline(admin.StackedInline):
    model = Module
    extra = 0
    fields = ('title', 'description', 'order')


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 0
    fields = ('title', 'description', 'file', 'url')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_course_count')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_course_count(self, obj):
        return obj.courses.count()
    get_course_count.short_description = _("Courses")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'difficulty', 'status', 'created_at', 'get_module_count')
    list_filter = ('status', 'difficulty', 'category', 'created_at')
    search_fields = ('title', 'description', 'instructor__username', 'instructor__email')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
    date_hierarchy = 'created_at'
    
    def get_module_count(self, obj):
        return obj.modules.count()
    get_module_count.short_description = _("Modules")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'get_lesson_count')
    list_filter = ('course__title',)
    search_fields = ('title', 'description', 'course__title')
    inlines = [LessonInline]
    
    def get_lesson_count(self, obj):
        return obj.lessons.count()
    get_lesson_count.short_description = _("Lessons")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'duration', 'order', 'is_required')
    list_filter = ('content_type', 'is_required', 'module__course__title')
    search_fields = ('title', 'content', 'module__title', 'module__course__title')
    inlines = [ResourceInline]
    
    def get_course(self, obj):
        return obj.module.course.title
    get_course.short_description = _("Course")


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'get_course')
    list_filter = ('lesson__module__course__title',)
    search_fields = ('title', 'description', 'lesson__title')
    
    def get_course(self, obj):
        return obj.lesson.module.course.title
    get_course.short_description = _("Course")