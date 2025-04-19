# accounts/context_processors.py
def user_context(request):
    """Add user type information to context"""
    context = {}
    if request.user.is_authenticated:
        context['is_admin'] = request.user.is_admin_user()
        context['is_teacher'] = request.user.is_teacher()
        context['is_student'] = request.user.is_student()
    return context