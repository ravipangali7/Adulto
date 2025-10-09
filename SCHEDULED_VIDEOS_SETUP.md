# Scheduled Videos Setup Guide

This guide explains how to set up the video scheduling system for your VPS deployment with Gunicorn.

## Features Implemented

### 1. Video Status System
- **Published**: Video is live and visible to users (`is_active = True`)
- **Draft**: Video is saved but not published (`is_active = False`, no schedule)
- **Scheduled**: Video will be published at a specific time (`is_active = False`, `scheduled_publish_at` set)

### 2. Video Form Updates
- Radio button options for publishing:
  - **Publish Now**: Makes video immediately active
  - **Save as Draft**: Saves video but keeps it inactive
  - **Schedule**: Sets a future publish date/time
- Dynamic schedule date/time picker (shows only when "Schedule" is selected)

### 3. Video List Updates
- Status badges show: Published, Scheduled, or Draft
- Scheduled videos show the scheduled publish time instead of creation date
- Color-coded status indicators

## VPS Deployment Setup

### Option 1: Cron Job (Recommended for simple setup)

1. **Create a cron job** to run the management command every minute:
```bash
# Edit crontab
crontab -e

# Add this line to run every minute
* * * * * cd /path/to/your/project && /path/to/your/venv/bin/python manage.py publish_scheduled_videos
```

2. **For more frequent checking** (every 30 seconds), you can use:
```bash
# Run every 30 seconds
* * * * * cd /path/to/your/project && /path/to/your/venv/bin/python manage.py publish_scheduled_videos
* * * * * sleep 30; cd /path/to/your/project && /path/to/your/venv/bin/python manage.py publish_scheduled_videos
```

### Option 2: Celery with Celery Beat (Advanced)

1. **Install Celery and Redis**:
```bash
pip install celery redis
```

2. **Add to your settings.py**:
```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'publish-scheduled-videos': {
        'task': 'core.tasks.publish_scheduled_videos',
        'schedule': 60.0,  # Run every 60 seconds
    },
}
```

3. **Start Celery worker and beat**:
```bash
# Terminal 1 - Celery Worker
celery -A adulto worker --loglevel=info

# Terminal 2 - Celery Beat
celery -A adulto beat --loglevel=info
```

### Option 3: Systemd Service (Production)

1. **Create a systemd service file** `/etc/systemd/system/video-scheduler.service`:
```ini
[Unit]
Description=Video Scheduler Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/project
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/python manage.py publish_scheduled_videos
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

2. **Enable and start the service**:
```bash
sudo systemctl enable video-scheduler.service
sudo systemctl start video-scheduler.service
```

## Testing the Setup

1. **Create a test scheduled video**:
   - Go to video creation form
   - Select "Schedule" option
   - Set a time 1-2 minutes in the future
   - Save the video

2. **Check the video status**:
   - Video should show as "Scheduled" in the video list
   - Wait for the scheduled time
   - Video should automatically become "Published"

3. **Check logs**:
   - For cron jobs: Check `/var/log/cron` or `journalctl -u cron`
   - For Celery: Check Celery worker logs
   - For systemd: Check `journalctl -u video-scheduler`

## Database Migration

The system adds a new field `scheduled_publish_at` to the Video model. Make sure to run:

```bash
python manage.py migrate
```

## Monitoring

### Check Scheduled Videos
```bash
# List all scheduled videos
python manage.py shell
>>> from core.models import Video
>>> from django.utils import timezone
>>> Video.objects.filter(is_active=False, scheduled_publish_at__isnull=False)
```

### Manual Publishing
```bash
# Manually run the publishing command
python manage.py publish_scheduled_videos
```

## Troubleshooting

### Common Issues

1. **Timezone Issues**: Make sure your server timezone matches your Django `TIME_ZONE` setting
2. **Permission Issues**: Ensure the cron/systemd user has access to your project directory
3. **Python Path**: Make sure the full path to Python is used in cron jobs
4. **Database Access**: Ensure the user can access the database

### Debug Mode
Add logging to see what's happening:
```python
# In your settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/path/to/your/project/scheduler.log',
        },
    },
    'loggers': {
        'core.management.commands.publish_scheduled_videos': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Security Considerations

1. **Cron Job Security**: Use absolute paths and proper user permissions
2. **Database Security**: Ensure proper database user permissions
3. **Log Security**: Secure log files with appropriate permissions
4. **Error Handling**: The system includes error handling to prevent crashes

## Performance

- The management command is lightweight and only processes videos that are ready to publish
- Database queries are optimized to only fetch necessary videos
- No impact on site performance as it runs in the background
