# courses/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from accounts.models import User


class Category(models.Model):
    """Course category model"""
    name = models.CharField(max_length=100, verbose_name=_("Category Name"))
    slug = models.SlugField(unique=True, verbose_name=_("URL Slug"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    icon = models.CharField(max_length=50, blank=True, verbose_name=_("Icon Class"))
    
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])


class Course(models.Model):
    """Course model"""
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('archived', _('Archived')),
    )
    DIFFICULTY_CHOICES = (
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
    )
    
    title = models.CharField(max_length=200, verbose_name=_("Course Title"))
    slug = models.SlugField(unique=True, verbose_name=_("URL Slug"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses', verbose_name=_("Category"))
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught', verbose_name=_("Instructor"))
    description = models.TextField(verbose_name=_("Description"))
    learning_objectives = models.TextField(blank=True, verbose_name=_("Learning Objectives"))
    prerequisites = models.TextField(blank=True, verbose_name=_("Prerequisites"))
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True, verbose_name=_("Thumbnail"))
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner', verbose_name=_("Difficulty Level"))
    duration = models.PositiveIntegerField(help_text=_("Duration in hours"), null=True, blank=True, verbose_name=_("Duration"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    published_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Published At"))
    
    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('course_detail', args=[self.slug])
    
    @property
    def total_modules(self):
        return self.modules.count()
    
    @property
    def total_lessons(self):
        return sum(module.lessons.count() for module in self.modules.all())


class Module(models.Model):
    """Course module model"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name=_("Course"))
    title = models.CharField(max_length=200, verbose_name=_("Module Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    
    class Meta:
        verbose_name = _("Module")
        verbose_name_plural = _("Modules")
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """Lesson model"""
    CONTENT_TYPE_CHOICES = (
        ('text', _('Text')),
        ('video', _('Video')),
        ('assignment', _('Assignment')),
    )
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', verbose_name=_("Module"))
    title = models.CharField(max_length=200, verbose_name=_("Lesson Title"))
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='text', verbose_name=_("Content Type"))
    content = models.TextField(verbose_name=_("Content"))
    video_url = models.URLField(blank=True, null=True, verbose_name=_("Video URL"))
    duration = models.PositiveIntegerField(help_text=_("Duration in minutes"), null=True, blank=True, verbose_name=_("Duration"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    is_required = models.BooleanField(default=True, verbose_name=_("Required"))
    
    class Meta:
        verbose_name = _("Lesson")
        verbose_name_plural = _("Lessons")
        ordering = ['order']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('lesson_detail', args=[self.module.course.slug, self.id])


class Resource(models.Model):
    """Additional resource model for lessons"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources', verbose_name=_("Lesson"))
    title = models.CharField(max_length=200, verbose_name=_("Resource Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    file = models.FileField(upload_to='lesson_resources/', blank=True, null=True, verbose_name=_("File"))
    url = models.URLField(blank=True, null=True, verbose_name=_("URL"))
    
    class Meta:
        verbose_name = _("Resource")
        verbose_name_plural = _("Resources")
    
    def __str__(self):
        return self.title