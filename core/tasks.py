from django.utils import timezone
from core.models import Video
import logging
import threading
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def publish_scheduled_videos():
    """
    Task to publish videos that are scheduled for release.
    This function checks for videos that should be published now.
    """
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
            # Keep scheduled_publish_at to preserve the scheduled date for display
            video.save()
            
            published_count += 1
            logger.info(f'Published scheduled video: {video.title} (ID: {video.id})')
            
        except Exception as e:
            logger.error(f'Error publishing video {video.title} (ID: {video.id}): {str(e)}')
    
    return f'Published {published_count} video(s)'

class VideoScheduler:
    """
    A simple video scheduler that runs in a background thread.
    This replaces the need for external task queues.
    """
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler in a background thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Check for videos to publish every 10 seconds
                publish_scheduled_videos()
                time.sleep(10)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait longer on error

# Global scheduler instance
scheduler = VideoScheduler()

def start_video_scheduler():
    """Start the video scheduler"""
    if not scheduler.running:
        scheduler.start()

def stop_video_scheduler():
    """Stop the video scheduler"""
    if scheduler.running:
        scheduler.stop()