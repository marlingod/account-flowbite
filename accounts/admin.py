# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'get_groups', 'is_active')
    list_filter = ('groups', 'user_type', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 'bio', 'phone_number', 'date_of_birth')}),
        (_('Role'), {'fields': ('user_type', 'groups')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2'),
        }),
    )
    
    # Define additional actions
    actions = ['activate_users', 'deactivate_users']
    
    def get_groups(self, obj):
        """Display user groups in the admin list view"""
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = _("Groups")
    
    def activate_users(self, request, queryset):
        """Admin action to activate selected users"""
        queryset.update(is_active=True)
    activate_users.short_description = _("Activate selected users")
    
    def deactivate_users(self, request, queryset):
        """Admin action to deactivate selected users"""
        queryset.update(is_active=False)
    deactivate_users.short_description = _("Deactivate selected users")

admin.site.register(User, CustomUserAdmin)