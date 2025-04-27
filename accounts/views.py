# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import User
from .forms import UserProfileForm, ProfilePictureForm, CreateUserForm
from .decorators import admin_required

@login_required
def profile_view(request):
    """View the user's own profile"""
    return render(request, 'accounts/profile.html', {'profile_user': request.user})

@login_required
def edit_profile(request):
    """Edit user profile information"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        picture_form = ProfilePictureForm(request.POST, request.FILES, instance=user)
        
        if 'update_info' in request.POST and form.is_valid():
            form.save()
            messages.success(request, _("Your profile information has been updated."))
            return redirect('profile')
            
        elif 'update_picture' in request.POST and picture_form.is_valid():
            picture_form.save()
            messages.success(request, _("Your profile picture has been updated."))
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
        picture_form = ProfilePictureForm(instance=user)
    
    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'picture_form': picture_form
    })

@admin_required
def user_list(request):
    """Display a list of users (admin only)"""
    # Get query parameters for filtering
    user_type = request.GET.get('user_type', '')
    is_active = request.GET.get('is_active', '')
    search_query = request.GET.get('q', '')
    
    # Start with all users
    users = User.objects.all()
    
    # Apply filters
    if user_type:
        users = users.filter(user_type=user_type)
    
    if is_active == 'false':
        users = users.filter(is_active=False)
    elif is_active == 'true' or not is_active:
        users = users.filter(is_active=True)
    
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )
    
    # Order by username
    users = users.order_by('username')
    
    return render(request, 'accounts/user_list.html', {'users': users})

@admin_required
def user_detail(request, user_id):
    """View a specific user's profile (admin only)"""
    profile_user = get_object_or_404(User, id=user_id)
    return render(request, 'accounts/user_detail.html', {'profile_user': profile_user})

@admin_required
def change_user_type(request, user_id):
    """Change a user's type (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_user_type = request.POST.get('user_type')
        if new_user_type in dict(User.USER_TYPE_CHOICES).keys():
            user.user_type = new_user_type
            user.save()
            messages.success(request, _("User type updated successfully."))
            return redirect('user_detail', user_id=user.id)
        else:
            messages.error(request, _("Invalid user type."))
    
    return render(request, 'accounts/change_user_type.html', {'profile_user': user})

@admin_required
def toggle_user_active(request, user_id):
    """Toggle a user's active status (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deactivating your own account
    if user.id == request.user.id:
        messages.error(request, _("You cannot deactivate your own account."))
        return redirect('user_detail', user_id=user.id)
    
    # Toggle the is_active flag
    user.is_active = not user.is_active
    user.save()
    
    action = "activated" if user.is_active else "deactivated"
    messages.success(request, _(f"User account has been {action}."))
    
    return redirect('user_detail', user_id=user.id)



# Additional Admin Views # accounts/views.py (additional admin views)
@login_required
def create_user(request):
    """Create a new user (admin only)"""
    if not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Set a random password that the user will reset
            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()
            
            # Send welcome email with password reset link
            try:
                send_welcome_email(user, request)
                messages.success(request, _("User created successfully. A welcome email has been sent."))
            except Exception as e:
                messages.warning(request, _("User created, but there was an error sending the welcome email."))
            
            return redirect('user_list')
    else:
        form = CreateUserForm()
    
    return render(request, 'accounts/create_user.html', {'form': form})

@login_required
def change_user_type(request, user_id):
    """Change a user's type (admin only)"""
    if not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = ChangeUserTypeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("User type updated successfully."))
            return redirect('user_detail', user_id=user.id)
    else:
        form = ChangeUserTypeForm(instance=user)
    
    return render(request, 'accounts/change_user_type.html', {
        'form': form,
        'profile_user': user
    })

@login_required
def deactivate_user(request, user_id):
    """Deactivate a user account (admin only)"""
    if not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deactivation
    if user.id == request.user.id:
        messages.error(request, _("You cannot deactivate your own account."))
        return redirect('user_detail', user_id=user.id)
    
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, _("User account has been deactivated."))
        return redirect('user_list')
    
    return render(request, 'accounts/deactivate_user.html', {'profile_user': user})

@login_required
def activate_user(request, user_id):
    """Reactivate a user account (admin only)"""
    if not request.user.is_admin_user():
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = True
        user.save()
        messages.success(request, _("User account has been activated."))
        return redirect('user_list')
    
    return render(request, 'accounts/activate_user.html', {'profile_user': user})