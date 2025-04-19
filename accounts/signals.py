# accounts/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User

@receiver(pre_save, sender=User)
def handle_user_type_change(sender, instance, **kwargs):
    """Handle changes to user_type field by updating group membership"""
    if instance.pk:  # Only for existing users (not new users)
        try:
            # Get the old instance from the database
            old_instance = User.objects.get(pk=instance.pk)
            
            # If user type has changed, update group membership
            if old_instance.user_type != instance.user_type:
                # Create groups if they don't exist
                admin_group = Group.objects.get_or_create(name='Administrators')[0]
                teacher_group = Group.objects.get_or_create(name='Teachers')[0]
                student_group = Group.objects.get_or_create(name='Students')[0]
                
                # Remove from all role groups
                instance.groups.remove(admin_group, teacher_group, student_group)
                
                # Add to the appropriate group based on new user_type
                if instance.user_type == 'admin':
                    instance.groups.add(admin_group)
                    # Make admin users staff by default
                    instance.is_staff = True
                elif instance.user_type == 'teacher':
                    instance.groups.add(teacher_group)
                elif instance.user_type == 'student':
                    instance.groups.add(student_group)
        except User.DoesNotExist:
            pass

@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance, created, **kwargs):
    """Assign newly created users to the appropriate group based on user_type"""
    if created:  # Only for newly created users
        # Get or create the appropriate groups
        admin_group, _ = Group.objects.get_or_create(name='Administrators')
        teacher_group, _ = Group.objects.get_or_create(name='Teachers')
        student_group, _ = Group.objects.get_or_create(name='Students')
        
        # Assign user to appropriate group
        if instance.user_type == 'admin':
            instance.groups.add(admin_group)
            # Make admin users staff by default
            if not instance.is_staff:
                instance.is_staff = True
                instance.save(update_fields=['is_staff'])
        elif instance.user_type == 'teacher':
            instance.groups.add(teacher_group)
        else:  # Default to student
            instance.groups.add(student_group)