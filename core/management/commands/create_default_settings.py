from django.core.management.base import BaseCommand
from core.models import Settings


class Command(BaseCommand):
    help = 'Create default settings for the site'

    def handle(self, *args, **options):
        # Default settings
        default_settings = [
            {
                'key': 'site_title',
                'value': 'Adulto',
                'description': 'The main title of the website'
            },
            {
                'key': 'site_description',
                'value': 'Your premier destination for high-quality video content. Discover, watch, and share amazing videos across various categories.',
                'description': 'The main description of the website'
            },
            {
                'key': 'contact_email',
                'value': 'contact@adulto.com',
                'description': 'Contact email address'
            },
            {
                'key': 'contact_phone',
                'value': '+1 (555) 123-4567',
                'description': 'Contact phone number'
            },
            {
                'key': 'social_facebook',
                'value': 'https://facebook.com/adulto',
                'description': 'Facebook page URL'
            },
            {
                'key': 'social_twitter',
                'value': 'https://twitter.com/adulto',
                'description': 'Twitter profile URL'
            },
            {
                'key': 'social_instagram',
                'value': 'https://instagram.com/adulto',
                'description': 'Instagram profile URL'
            },
            {
                'key': 'footer_text',
                'value': 'Made with ❤️ for video lovers',
                'description': 'Footer text message'
            }
        ]

        created_count = 0
        updated_count = 0

        for setting_data in default_settings:
            setting, created = Settings.objects.get_or_create(
                key=setting_data['key'],
                defaults={
                    'value': setting_data['value'],
                    'description': setting_data['description']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created setting: {setting.key}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Setting already exists: {setting.key}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(default_settings)} settings. '
                f'Created: {created_count}, Already existed: {updated_count}'
            )
        )
