# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

    
class User(AbstractUser):

    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES, 
        default='student',
        verbose_name=_("User Type")
    )
    bio = models.TextField(blank=True, verbose_name=_("Biography"))
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        verbose_name=_("Profile Picture")
    )
    phone_number = models.CharField(max_length=20, blank=True, verbose_name=_("Phone Number"))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_("Date of Birth"))
    
    # Helper methods for checking user type
    def is_admin_user(self):
        return self.groups.filter(name='Administrators').exists()
    
    def is_teacher(self):
        return self.groups.filter(name='Teachers').exists()
    
    def is_student(self):
        return self.groups.filter(name='Students').exists()
    
    # Get user initials for avatar placeholders
    def get_initials(self):
        initials = ""
        if self.first_name:
            initials += self.first_name[0]
        if self.last_name:
            initials += self.last_name[0]
        if not initials and self.username:
            initials = self.username[0]
        return initials.upper()
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")