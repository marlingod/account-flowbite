# enrollment/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User
from courses.models import Course


class Enrollment(models.Model):
    """Model representing a student's enrollment in a course"""
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('dropped', _('Dropped')),
    )
    
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        verbose_name=_("Student")
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        verbose_name=_("Course")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name=_("Status")
    )
    enrolled_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Enrolled At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Updated")
    )
    completion_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_("Completion Date")
    )
    progress = models.FloatField(
        default=0,
        help_text=_("Percentage of course completed"),
        verbose_name=_("Progress")
    )
    
    class Meta:
        verbose_name = _("Enrollment")
        verbose_name_plural = _("Enrollments")
        unique_together = ('student', 'course')
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title}"
    
    def complete_enrollment(self):
        """Mark enrollment as completed"""
        self.status = 'completed'
        self.completion_date = timezone.now()
        self.progress = 100
        self.save()
    
    def drop_enrollment(self):
        """Mark enrollment as dropped"""
        self.status = 'dropped'
        self.save()
    
    def activate_enrollment(self):
        """Mark enrollment as active"""
        self.status = 'active'
        self.save()


class LessonProgress(models.Model):
    """Model to track student progress through lessons"""
    enrollment = models.ForeignKey(
        Enrollment, 
        on_delete=models.CASCADE, 
        related_name='lesson_progress',
        verbose_name=_("Enrollment")
    )
    lesson = models.ForeignKey(
        'courses.Lesson', 
        on_delete=models.CASCADE, 
        related_name='student_progress',
        verbose_name=_("Lesson")
    )
    status = models.CharField(
        max_length=20, 
        choices=(
            ('not_started', _('Not Started')),
            ('in_progress', _('In Progress')),
            ('completed', _('Completed')),
        ),
        default='not_started',
        verbose_name=_("Status")
    )
    last_accessed = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_("Last Accessed")
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_("Completed At")
    )
    
    class Meta:
        verbose_name = _("Lesson Progress")
        verbose_name_plural = _("Lesson Progress")
        unique_together = ('enrollment', 'lesson')
        ordering = ['lesson__module__order', 'lesson__order']
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.lesson.title}"
    
    def mark_as_started(self):
        """Mark lesson as in progress"""
        self.status = 'in_progress'
        self.last_accessed = timezone.now()
        self.save()
    
    def mark_as_completed(self):
        """Mark lesson as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        # Update enrollment progress
        self.update_enrollment_progress()
    
    def update_enrollment_progress(self):
        """Update the overall enrollment progress"""
        enrollment = self.enrollment
        total_lessons = enrollment.course.total_lessons
        completed_lessons = LessonProgress.objects.filter(
            enrollment=enrollment,
            status='completed'
        ).count()
        
        if total_lessons > 0:
            progress = (completed_lessons / total_lessons) * 100
            enrollment.progress = progress
            
            # If progress is 100%, mark enrollment as completed
            if progress >= 100:
                enrollment.complete_enrollment()
            else:
                enrollment.save()