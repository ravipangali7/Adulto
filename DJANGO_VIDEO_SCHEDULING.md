# Django Video Scheduling System

## Overview
This system provides video scheduling functionality using pure Django without external dependencies like cron jobs, Redis, or Celery.

## How It Works

### 1. Background Scheduler
- A background thread runs automatically when Django starts
- Checks for scheduled videos every 30 seconds
- Publishes videos when their scheduled time arrives
- Runs as a daemon thread (stops when Django stops)

### 2. Video Scheduling
- Videos can be scheduled during creation or editing
- Uses the existing `scheduled_publish_at` field in the Video model
- Videos remain inactive (`is_active=False`) until scheduled time
- Once published, `scheduled_publish_at` is cleared

### 3. Automatic Publishing
- Videos are automatically published when `scheduled_publish_at <= now()`
- The video becomes active (`is_active=True`)
- Scheduled time is cleared to prevent re-publishing

## Configuration

### Settings
```python
# In settings.py
VIDEO_SCHEDULING_ENABLED = True  # Enable/disable scheduling
```

### App Configuration
The scheduler starts automatically when Django starts (in `core/apps.py`):
```python
def ready(self):
    if getattr(settings, 'VIDEO_SCHEDULING_ENABLED', False):
        from core.tasks import start_video_scheduler
        start_video_scheduler()
```

## Usage

### 1. Schedule a Video
When creating or editing a video:
1. Select "Schedule" publishing option
2. Choose date and time for publication
3. Save the video
4. Video will be published automatically at the scheduled time

### 2. Manual Check
Run the management command to manually check for scheduled videos:
```bash
python manage.py check_scheduled_videos
```

### 3. Monitor Logs
Check Django logs for scheduling activity:
```
Published scheduled video: Video Title (ID: 123)
```

## Files Modified

### Core Files
- `core/tasks.py` - Background scheduler and publishing logic
- `core/apps.py` - Auto-start scheduler on Django startup
- `core/forms.py` - Video form with scheduling options
- `core/models.py` - Video model with scheduling fields

### Management Commands
- `core/management/commands/check_scheduled_videos.py` - Manual check command

### Settings
- `adulto/settings.py` - Added `VIDEO_SCHEDULING_ENABLED` setting

## Benefits

### ✅ Advantages
- **No External Dependencies** - Pure Django solution
- **Automatic Startup** - Starts with Django server
- **Simple Configuration** - Just enable/disable in settings
- **Real-time Monitoring** - Check logs for activity
- **Manual Override** - Management command for manual checks

### ⚠️ Considerations
- **Single Server** - Scheduler runs on one server instance
- **Memory Usage** - Background thread uses minimal memory
- **30-Second Delay** - Maximum delay between check and publish
- **Development Mode** - May restart frequently in development

## Production Deployment

### For Production
1. **Enable Scheduling**: Set `VIDEO_SCHEDULING_ENABLED = True`
2. **Monitor Logs**: Check for scheduling activity
3. **Single Instance**: Ensure only one Django instance runs the scheduler
4. **Backup Plan**: Keep the manual command as backup

### Alternative for High-Volume
For high-volume sites, consider:
- **Celery** with Redis/RabbitMQ
- **Django-RQ** with Redis
- **Cron jobs** with management commands

## Troubleshooting

### Scheduler Not Starting
1. Check `VIDEO_SCHEDULING_ENABLED = True` in settings
2. Check Django logs for errors
3. Restart Django server

### Videos Not Publishing
1. Run manual check: `python manage.py check_scheduled_videos`
2. Check video `scheduled_publish_at` field
3. Verify timezone settings

### Performance Issues
1. Increase check interval in `core/tasks.py` (currently 30 seconds)
2. Add database indexing on `scheduled_publish_at` field
3. Consider moving to Celery for high volume

## Example Usage

### Schedule Video for Tomorrow
```python
from django.utils import timezone
from datetime import timedelta

video = Video.objects.get(id=1)
video.scheduled_publish_at = timezone.now() + timedelta(days=1)
video.is_active = False
video.save()
# Video will be published automatically tomorrow
```

### Check Scheduled Videos
```python
from core.tasks import publish_scheduled_videos
result = publish_scheduled_videos()
print(result)  # "Published 2 video(s)"
```

This system provides a robust, Django-native solution for video scheduling without external dependencies!
