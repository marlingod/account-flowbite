# enrollment/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Enrollment, LessonProgress


class LessonProgressInline(admin.TabularInline):
    model = LessonProgress
    extra = 0
    readonly_fields = ('lesson', 'status', 'last_accessed', 'completed_at')
    can_delete = False
    max_num = 0  # Don't allow adding lesson progress manually


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrolled_at', 'progress')
    list_filter = ('status', 'enrolled_at', 'course__title')
    search_fields = ('student__username', 'student__email', 'student__first_name', 
                    'student__last_name', 'course__title')
    date_hierarchy = 'enrolled_at'
    readonly_fields = ('enrolled_at', 'progress')
    inlines = [LessonProgressInline]
    
    actions = ['activate_enrollments', 'mark_as_completed', 'drop_enrollments']
    
    def activate_enrollments(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, _(f"{updated} enrollments were successfully marked as active."))
    activate_enrollments.short_description = _("Mark selected enrollments as active")
    
    def mark_as_completed(self, request, queryset):
        for enrollment in queryset:
            enrollment.complete_enrollment()
        self.message_user(request, _(f"{queryset.count()} enrollments were successfully marked as completed."))
    mark_as_completed.short_description = _("Mark selected enrollments as completed")
    
    def drop_enrollments(self, request, queryset):
        updated = queryset.update(status='dropped')
        self.message_user(request, _(f"{updated} enrollments were successfully marked as dropped."))
    drop_enrollments.short_description = _("Mark selected enrollments as dropped")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'status', 'last_accessed', 'completed_at')
    list_filter = ('status', 'last_accessed', 'enrollment__course__title')
    search_fields = ('enrollment__student__username', 'enrollment__student__email', 
                    'lesson__title', 'enrollment__course__title')
    date_hierarchy = 'last_accessed'
    readonly_fields = ('last_accessed', 'completed_at')
    
    actions = ['mark_as_completed', 'mark_as_in_progress', 'mark_as_not_started']
    
    def mark_as_completed(self, request, queryset):
        for progress in queryset:
            progress.mark_as_completed()
        self.message_user(request, _(f"{queryset.count()} lesson progress entries were successfully marked as completed."))
    mark_as_completed.short_description = _("Mark selected lessons as completed")
    
    def mark_as_in_progress(self, request, queryset):
        for progress in queryset:
            progress.mark_as_started()
        self.message_user(request, _(f"{queryset.count()} lesson progress entries were successfully marked as in progress."))
    mark_as_in_progress.short_description = _("Mark selected lessons as in progress")
    
    def mark_as_not_started(self, request, queryset):
        updated = queryset.update(status='not_started')
        self.message_user(request, _(f"{updated} lesson progress entries were successfully marked as not started."))
    mark_as_not_started.short_description = _("Mark selected lessons as not started")