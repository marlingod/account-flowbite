# accounts/adapters.py
from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        This is called when saving user via allauth registration.
        We override this to set additional data on user object.
        """
        # Get the standard data from the form
        user = super().save_user(request, user, form, commit=False)
        
        # Get additional user data from the form if present
        if hasattr(form, 'cleaned_data'):
            user_type = form.cleaned_data.get('user_type', 'student')
            first_name = form.cleaned_data.get('first_name', '')
            last_name = form.cleaned_data.get('last_name', '')
            
            user.user_type = user_type
            user.first_name = first_name
            user.last_name = last_name
        
        if commit:
            user.save()
        
        return user
    
    def send_mail(self, template_prefix, email, context):
        """
        Override the send_mail method to use our custom email templates.
        """
        subject = render_to_string(f'{template_prefix}_subject.txt', context)
        # Force subject to a single line to avoid header injection issues
        subject = ''.join(subject.splitlines())
        
        # Render content
        html_content = render_to_string(f'{template_prefix}_message.html', context)
        text_content = render_to_string(f'{template_prefix}_message.txt', context)
        
        # Create the email message
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()