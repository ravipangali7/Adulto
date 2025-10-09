from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.signals import request_started
from .models import Video
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Video)
def extract_video_duration(sender, instance, created, **kwargs):
    """
    Automatically extract video duration when a video is saved
    """
    if instance.video_file and (created or not instance.duration):
        try:
            instance.extract_duration()
        except Exception as e:
            logger.error(f"Error extracting duration for video {instance.title}: {e}")

@receiver(request_started)
def ensure_scheduler_running(sender, **kwargs):
    """
    Ensure video scheduler is running when Django starts handling requests
    """
    try:
        from .tasks import start_video_scheduler
        start_video_scheduler()
    except Exception as e:
        logger.error(f"Failed to start video scheduler: {e}")
