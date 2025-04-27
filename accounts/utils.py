# accounts/utils.py
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

def send_welcome_email(user, request):
    """
    Send a welcome email to newly created users with password reset link
    """
    # Generate token for password reset
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build the password reset URL
    reset_url = f"{settings.BASE_URL}/accounts/password/reset/key/{uid}/{token}/"
    
    # Set up the context for email template
    context = {
        'user': user,
        'reset_url': reset_url,
        'site_name': request.site.name if hasattr(request, 'site') else 'LMS Platform',
    }
    
    # Render email content
    subject = _("Welcome to the LMS Platform")
    text_content = render_to_string('accounts/email/welcome_email.txt', context)
    html_content = render_to_string('accounts/email/welcome_email.html', context)
    
    # Create and send the email
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()