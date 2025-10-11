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

@receiver(post_save, sender=Video)
def generate_video_thumbnail(sender, instance, created, update_fields, **kwargs):
    """
    Automatically generate thumbnail when a video is created and no thumbnail exists
    """
    logger.info(f"=== SIGNAL FIRED for video: {instance.title} ===")
    logger.info(f"created={created}, update_fields={update_fields}")
    logger.info(f"Has thumbnail: {bool(instance.thumbnail)}")
    logger.info(f"Has video_file: {bool(instance.video_file)}")
    
    # Don't generate if thumbnail is being explicitly saved
    if update_fields and 'thumbnail' in update_fields:
        logger.info("SKIP: thumbnail in update_fields")
        return
    
    # Don't generate if thumbnail already exists (user provided one)
    if instance.thumbnail:
        logger.info("SKIP: thumbnail already exists")
        return
    
    # Only generate for newly created videos with video files
    if created and instance.video_file:
        logger.info("GENERATING thumbnail...")
        try:
            if instance.generate_thumbnail():
                instance.save(update_fields=['thumbnail'])
                logger.info(f"Generated thumbnail for video {instance.title}")
        except Exception as e:
            logger.error(f"Error generating thumbnail for video {instance.title}: {e}")
    else:
        logger.info(f"SKIP: created={created}, has_video_file={bool(instance.video_file)}")

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
