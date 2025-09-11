from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse


def send_verification_email(user, request):
    """Send email verification to user"""
    token = user.generate_email_verification_token()
    
    # Create activation URL
    activation_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': token})
    )
    
    # Get site title from settings or context
    site_title = getattr(settings, 'SITE_TITLE', 'Adulto')
    
    # Render email templates
    html_content = render_to_string('emails/email_verification.html', {
        'user': user,
        'activation_url': activation_url,
        'site_title': site_title,
    })
    
    text_content = render_to_string('emails/email_verification.txt', {
        'user': user,
        'activation_url': activation_url,
        'site_title': site_title,
    })
    
    # Send email
    try:
        send_mail(
            subject=f'Activate Your Account - {site_title}',
            message=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@adulto.com'),
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False
