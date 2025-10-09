from django.core.management.base import BaseCommand
from core.tasks import start_video_scheduler, scheduler

class Command(BaseCommand):
    help = 'Start the video scheduler manually'

    def handle(self, *args, **options):
        if scheduler.running:
            self.stdout.write('Video scheduler is already running')
        else:
            start_video_scheduler()
            self.stdout.write('Video scheduler started successfully')
        
        self.stdout.write(f'Scheduler status: {"Running" if scheduler.running else "Stopped"}')
