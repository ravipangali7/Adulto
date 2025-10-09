from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals
        
        # Start video scheduler if enabled
        if getattr(settings, 'VIDEO_SCHEDULING_ENABLED', False):
            from core.tasks import start_video_scheduler
            start_video_scheduler()