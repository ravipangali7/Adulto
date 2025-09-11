from django.core.management.base import BaseCommand
from core.models import AgeVerification


class Command(BaseCommand):
    help = 'Create default age verification modal'

    def handle(self, *args, **options):
        # Default age verification content
        default_content = """
        <p>The content available on <strong>{{ site_name }}</strong> may contain pornographic materials.</p>
        
        <p><strong>{{ site_name }}</strong> is strictly limited to those over 18 or of legal age in your jurisdiction, whichever is greater.</p>
        
        <p>One of our core goals is to help parents restrict access to <strong>{{ site_name }}</strong> for minors, so we have ensured that <strong>{{ site_name }}</strong> is, and remains, fully compliant with the RTA (Restricted to Adults) code. This means that all access to the site can be blocked by simple parental control tools. It is important that responsible parents and guardians take the necessary steps to prevent minors from accessing unsuitable content online, especially age-restricted content.</p>
        
        <p>Anyone with a minor in their household or under their supervision should implement basic parental control protections, including computer hardware and device settings, software installation, or ISP filtering services, to block your minors from accessing inappropriate content.</p>
        """

        # Create or update age verification
        age_verification, created = AgeVerification.objects.get_or_create(
            site_name='Adulto',
            defaults={
                'title': 'Age Verification Required',
                'content': default_content,
                'confirm_text': 'I am 18 or older',
                'deny_text': 'I am under 18',
                'deny_redirect_url': 'https://www.google.com',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created age verification modal')
            )
        else:
            # Update existing
            age_verification.title = 'Age Verification Required'
            age_verification.content = default_content
            age_verification.confirm_text = 'I am 18 or older'
            age_verification.deny_text = 'I am under 18'
            age_verification.deny_redirect_url = 'https://www.google.com'
            age_verification.is_active = True
            age_verification.save()
            
            self.stdout.write(
                self.style.SUCCESS('Updated age verification modal')
            )
