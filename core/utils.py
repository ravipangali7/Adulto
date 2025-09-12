from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse


def send_verification_email(user, request):
    """Send email verification to user"""
    try:
        token = user.generate_email_verification_token()
        print(f"Generated token for {user.email}: {token}")
        
        # Create activation URL
        activation_url = request.build_absolute_uri(
            reverse('verify_email', kwargs={'token': token})
        )
        print(f"Activation URL: {activation_url}")
        
        # Get site title from settings or context
        site_title = getattr(settings, 'SITE_TITLE', 'Desi X Zone')
        
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
        print(f"Attempting to send email to {user.email}")
        print(f"From email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@adulto.com')}")
        print(f"SMTP settings: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        
        send_mail(
            subject=f'Activate Your Account - {site_title}',
            message=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@adulto.com'),
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        print(f"Email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"Error sending verification email to {user.email}: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False
