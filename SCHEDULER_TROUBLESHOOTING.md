# Video Scheduler Troubleshooting Guide

## Problem: Videos Not Publishing After Django Restart

### Root Cause
When Django restarts (development with `--noreload` or production deployment), the background scheduler thread stops and doesn't automatically restart.

### Solutions Implemented

#### 1. **Automatic Restart on Request** ✅
- Added `request_started` signal handler in `core/signals.py`
- Scheduler automatically restarts when Django handles the first request
- Works in both development and production

#### 2. **Manual Scheduler Control** ✅
- `python manage.py start_scheduler` - Start scheduler manually
- `python manage.py scheduler_status` - Check scheduler status
- `python manage.py check_scheduled_videos` - Manual publish check

#### 3. **Robust Scheduler Logic** ✅
- Prevents multiple scheduler instances
- Better error handling and logging
- 10-second check interval for faster response

## How to Use

### Check Scheduler Status
```bash
python manage.py scheduler_status
```
**Output:**
```
Scheduler Status: [RUNNING]
Scheduled Videos: 1
  - Video 9: My Video | Scheduled: 2025-10-09 10:13:00+00:00 | [WAITING]
```

### Start Scheduler Manually
```bash
python manage.py start_scheduler
```
**Output:**
```
Video scheduler started successfully
Scheduler status: Running
```

### Manual Publish Check
```bash
python manage.py check_scheduled_videos
```
**Output:**
```
Video check completed: Published 2 video(s)
```

## Testing the System

### 1. Create Test Video with Past Time
```python
from core.models import Video
from django.utils import timezone
from datetime import timedelta

video = Video.objects.create(
    title='Test Video',
    slug='test-video',
    description='Test',
    uploader_id=1,
    scheduled_publish_at=timezone.now() - timedelta(minutes=5),
    is_active=False
)
```

### 2. Check Status
```bash
python manage.py scheduler_status
```

### 3. Wait 10 Seconds
The scheduler checks every 10 seconds automatically.

### 4. Verify Publication
```python
video = Video.objects.get(id=video.id)
print(f"Active: {video.is_active}, Scheduled: {video.scheduled_publish_at}")
# Should show: Active: True, Scheduled: None
```

## Production Deployment

### For Production Servers

#### Option 1: Automatic (Recommended)
- Scheduler starts automatically on first request
- No additional setup needed
- Works with Gunicorn, uWSGI, etc.

#### Option 2: Manual Start
Add to your deployment script:
```bash
python manage.py start_scheduler
```

#### Option 3: Cron Backup
Add to crontab as backup:
```bash
# Check every minute
* * * * * cd /path/to/project && python manage.py check_scheduled_videos
```

## Monitoring

### Check Logs
Look for these log messages:
```
Video scheduler started - checking every 10 seconds
Found 1 videos ready for publishing
✅ Published scheduled video: My Video (ID: 123)
```

### Database Queries
```sql
-- Check scheduled videos
SELECT id, title, scheduled_publish_at, is_active 
FROM core_video 
WHERE is_active = FALSE AND scheduled_publish_at IS NOT NULL;

-- Check recently published videos
SELECT id, title, scheduled_publish_at, is_active, created_at 
FROM core_video 
WHERE is_active = TRUE AND scheduled_publish_at IS NULL
ORDER BY created_at DESC LIMIT 10;
```

## Common Issues

### Issue: Scheduler Not Running
**Symptoms:** Videos not publishing, status shows [STOPPED]
**Solution:**
```bash
python manage.py start_scheduler
```

### Issue: Videos Scheduled for Future
**Symptoms:** Videos show [WAITING] status
**Solution:** Wait for scheduled time or manually set past time for testing

### Issue: Multiple Scheduler Instances
**Symptoms:** Duplicate log messages
**Solution:** Restart Django server to reset scheduler

### Issue: Timezone Problems
**Symptoms:** Videos not publishing at expected time
**Solution:** Check Django timezone settings in `settings.py`

## Files Modified

### Core Files
- `core/tasks.py` - Enhanced scheduler with restart protection
- `core/signals.py` - Added request_started signal handler
- `core/apps.py` - Auto-start scheduler on Django startup

### Management Commands
- `core/management/commands/start_scheduler.py` - Manual start
- `core/management/commands/scheduler_status.py` - Status check
- `core/management/commands/check_scheduled_videos.py` - Manual publish

## Verification Steps

### 1. Check Scheduler is Running
```bash
python manage.py scheduler_status
```

### 2. Create Test Video
```bash
python manage.py shell -c "
from core.models import Video
from django.utils import timezone
from datetime import timedelta
video = Video.objects.create(
    title='Test Video',
    slug='test-video',
    description='Test',
    uploader_id=1,
    scheduled_publish_at=timezone.now() - timedelta(minutes=1),
    is_active=False
)
print(f'Created video {video.id}')
"
```

### 3. Wait and Check
```bash
# Wait 15 seconds, then check
python manage.py scheduler_status
```

### 4. Verify Publication
```bash
python manage.py shell -c "
from core.models import Video
video = Video.objects.get(slug='test-video')
print(f'Active: {video.is_active}, Scheduled: {video.scheduled_publish_at}')
"
```

## Success Indicators

✅ **Scheduler Status:** [RUNNING]  
✅ **Videos with past times:** Automatically published  
✅ **Logs show:** "Published scheduled video" messages  
✅ **Database:** `is_active=True`, `scheduled_publish_at=None`  

The system is now robust and handles Django restarts automatically! 🚀
