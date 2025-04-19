# accounts/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

def admin_required(view_func):
    """Decorator to check if the user is in the Administrators group"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin_user():
            return view_func(request, *args, **kwargs)
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('dashboard')
    return _wrapped_view

def teacher_required(view_func):
    """Decorator to check if the user is in the Teachers group"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_teacher() or request.user.is_admin_user()):
            return view_func(request, *args, **kwargs)
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('dashboard')
    return _wrapped_view

def student_required(view_func):
    """Decorator to check if the user is in the Students group"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_student():
            return view_func(request, *args, **kwargs)
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('dashboard')
    return _wrapped_view