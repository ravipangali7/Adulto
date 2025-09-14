from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Video


@receiver(post_save, sender=Video)
def extract_video_duration(sender, instance, created, **kwargs):
    """
    Automatically extract video duration when a video is saved
    """
    # if instance.video_file and (created or not instance.duration):
    #     try:
    #         instance.extract_duration()
    #     except Exception as e:
    #         print(f"Error extracting duration for video {instance.title}: {e}")
