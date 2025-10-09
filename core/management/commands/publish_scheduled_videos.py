from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Video
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Publish scheduled videos that have reached their scheduled time'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Find videos that are scheduled and ready to be published
        scheduled_videos = Video.objects.filter(
            is_active=False,
            scheduled_publish_at__isnull=False,
            scheduled_publish_at__lte=now
        )
        
        published_count = 0
        
        for video in scheduled_videos:
            try:
                video.is_active = True
                video.scheduled_publish_at = None  # Clear the scheduled time
                video.save()
                
                published_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully published video: {video.title} (ID: {video.id})'
                    )
                )
                logger.info(f'Published scheduled video: {video.title} (ID: {video.id})')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error publishing video {video.title} (ID: {video.id}): {str(e)}'
                    )
                )
                logger.error(f'Error publishing video {video.title} (ID: {video.id}): {str(e)}')
        
        if published_count == 0:
            self.stdout.write(
                self.style.WARNING('No scheduled videos found to publish.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully published {published_count} video(s).')
            )
