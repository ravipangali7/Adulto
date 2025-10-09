from django.core.management.base import BaseCommand
from core.tasks import publish_scheduled_videos

class Command(BaseCommand):
    help = 'Check and publish any videos that are scheduled for release'

    def handle(self, *args, **options):
        result = publish_scheduled_videos()
        self.stdout.write(
            self.style.SUCCESS(f'Video check completed: {result}')
        )
