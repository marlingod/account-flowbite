# courses/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, HTML
from .models import Course, Module, Lesson, Resource, Category


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'icon']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name'),
            Field('slug', placeholder='Leave blank to auto-generate'),
            Field('description', rows=4),
            Field('icon', placeholder='e.g., fa-book, fa-code'),
            Div(
                Submit('submit', _('Save'), css_class='btn-primary'),
                HTML('<a href="{% url \'category_list\' %}" class="btn btn-secondary">Cancel</a>'),
                css_class='flex gap-2 mt-4'
            )
        )

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if not slug:
            slug = slugify(self.cleaned_data['name'])
        return slug


class CourseForm(forms.ModelForm):
    """Form for creating and editing courses"""
    class Meta:
        model = Course
        fields = ['title', 'slug', 'category', 'description', 'learning_objectives', 
                 'prerequisites', 'thumbnail', 'difficulty', 'duration', 'status']
        
    def __init__(self, *args, **kwargs):
        # Extract current user from kwargs
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('title'),
            Field('slug', placeholder='Leave blank to auto-generate'),
            Field('category'),
            Field('description', rows=4),
            Field('learning_objectives', rows=4),
            Field('prerequisites', rows=4),
            Field('thumbnail'),
            Field('difficulty'),
            Field('duration'),
            Field('status'),
            Div(
                Submit('submit', _('Save'), css_class='btn-primary'),
                HTML('<a href="{% url \'course_list\' %}" class="btn btn-secondary">Cancel</a>'),
                css_class='flex gap-2 mt-4'
            )
        )
    
    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if not slug:
            slug = slugify(self.cleaned_data['title'])
        return slug
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and not instance.pk:  # Only set instructor on new courses
            instance.instructor = self.user
        if commit:
            instance.save()
        return instance


class ModuleForm(forms.ModelForm):
    """Form for creating and editing modules"""
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
    
    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('title'),
            Field('description', rows=3),
            Field('order'),
            Div(
                Submit('submit', _('Save'), css_class='btn-primary'),
                HTML('<a href="{% url \'course_detail\' slug=course.slug %}" class="btn btn-secondary">Cancel</a>'),
                css_class='flex gap-2 mt-4'
            )
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.course:
            instance.course = self.course
        if commit:
            instance.save()
        return instance


class LessonForm(forms.ModelForm):
    """Form for creating and editing lessons"""
    class Meta:
        model = Lesson
        fields = ['title', 'content_type', 'content', 'video_url', 'duration', 'order', 'is_required']
    
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('title'),
            Field('content_type'),
            Field('content', rows=6),
            Field('video_url'),
            Field('duration'),
            Field('order'),
            Field('is_required'),
            Div(
                Submit('submit', _('Save'), css_class='btn-primary'),
                HTML('<a href="{% url \'module_detail\' course_slug=module.course.slug module_id=module.id %}" class="btn btn-secondary">Cancel</a>'),
                css_class='flex gap-2 mt-4'
            )
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.module:
            instance.module = self.module
        if commit:
            instance.save()
        return instance


class ResourceForm(forms.ModelForm):
    """Form for creating and editing lesson resources"""
    class Meta:
        model = Resource
        fields = ['title', 'description', 'file', 'url']
    
    def __init__(self, *args, **kwargs):
        self.lesson = kwargs.pop('lesson', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('title'),
            Field('description', rows=3),
            Field('file'),
            Field('url'),
            Div(
                Submit('submit', _('Save'), css_class='btn-primary'),
                HTML('<a href="{% url \'lesson_detail\' course_slug=lesson.module.course.slug lesson_id=lesson.id %}" class="btn btn-secondary">Cancel</a>'),
                css_class='flex gap-2 mt-4'
            )
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.lesson:
            instance.lesson = self.lesson
        if commit:
            instance.save()
        return instance