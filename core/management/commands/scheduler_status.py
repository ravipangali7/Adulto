from django.core.management.base import BaseCommand
from core.tasks import scheduler
from core.models import Video
from django.utils import timezone

class Command(BaseCommand):
    help = 'Check video scheduler status and scheduled videos'

    def handle(self, *args, **options):
        # Check scheduler status
        status = "Running" if scheduler.running else "Stopped"
        self.stdout.write(f'Scheduler Status: {status}')
        
        # Check scheduled videos
        now = timezone.now()
        scheduled_videos = Video.objects.filter(
            is_active=False,
            scheduled_publish_at__isnull=False
        )
        
        self.stdout.write(f'Scheduled Videos: {scheduled_videos.count()}')
        
        for video in scheduled_videos:
            status = "Ready" if video.scheduled_publish_at <= now else "Waiting"
            self.stdout.write(
                f'  Video {video.id}: {video.title} | '
                f'Scheduled: {video.scheduled_publish_at} | {status}'
            )
        
        if not scheduled_videos.exists():
            self.stdout.write('  No scheduled videos found')
