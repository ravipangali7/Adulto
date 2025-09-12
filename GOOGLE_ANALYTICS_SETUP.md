# Google Analytics Setup Guide

This guide will help you set up Google Analytics 4 (GA4) in your Django project from start to finish.

## Prerequisites

- Django project with the `core` app
- Google account
- Access to Google Analytics

## Step 1: Create Google Analytics Account

1. Go to [Google Analytics](https://analytics.google.com/)
2. Click "Start measuring" or "Create Account"
3. Set up your account:
   - Account name: Your website name (e.g., "Adulto")
   - Property name: Your website URL
   - Industry category: Select appropriate category
   - Business size: Select appropriate size
4. Choose your data stream:
   - Select "Web"
   - Enter your website URL
   - Enter a stream name (e.g., "Adulto Website")
5. Copy your **Measurement ID** (starts with G-XXXXXXXXXX)

## Step 2: Install Dependencies

The project already includes the necessary dependencies, but if you're setting up from scratch:

```bash
pip install python-dotenv
```

## Step 3: Environment Configuration

1. Create a `.env` file in your project root (copy from `.env.example`):
```bash
cp .env.example .env
```

2. Edit the `.env` file with your Google Analytics settings:
```env
# Google Analytics
GOOGLE_ANALYTICS_TRACKING_ID=G-XXXXXXXXXX
GOOGLE_ANALYTICS_ENABLED=True
```

Replace `G-XXXXXXXXXX` with your actual Measurement ID from Google Analytics.

## Step 4: Django Settings

The following settings have been added to `adulto/settings.py`:

```python
# Google Analytics Configuration
GOOGLE_ANALYTICS_TRACKING_ID = os.getenv('GOOGLE_ANALYTICS_TRACKING_ID', '')
GOOGLE_ANALYTICS_ENABLED = os.getenv('GOOGLE_ANALYTICS_ENABLED', 'False').lower() == 'true'
```

## Step 5: Template Integration

### Base Template
The Google Analytics tracking code is automatically included in `templates/site/base.html`:

```html
<!-- Google Analytics -->
{% load analytics %}
{% google_analytics %}
```

### Custom Event Tracking
The project includes comprehensive event tracking for:

#### Video Interactions
- **Video Play**: When a video starts playing
- **Video Pause**: When a video is paused
- **Video Complete**: When a video finishes
- **Video Like**: When a user likes a video
- **Video Comment**: When a user comments on a video
- **Video Click**: When a user clicks on a video thumbnail
- **Fullscreen Events**: When entering/exiting fullscreen mode

#### Event Categories
All events are categorized as:
- `engagement`: User interaction events

## Step 6: Available Template Tags

### Basic Tracking
```html
{% load analytics %}
{% google_analytics %}
```

### Custom Events
```html
{% google_analytics_event 'event_name' 'category' 'label' %}
```

### Page Views
```html
{% google_analytics_page_view 'Page Title' 'https://example.com/page' %}
```

## Step 7: Testing Your Setup

1. Start your Django development server:
```bash
python manage.py runserver
```

2. Visit your website and perform actions that trigger events
3. Check Google Analytics Real-time reports:
   - Go to Google Analytics
   - Navigate to Reports > Realtime
   - You should see active users and events

## Step 8: Production Deployment

1. Set environment variables in your production environment:
```bash
export GOOGLE_ANALYTICS_TRACKING_ID="G-XXXXXXXXXX"
export GOOGLE_ANALYTICS_ENABLED="True"
```

2. Or add them to your production `.env` file

## Event Tracking Details

### Video Events
| Event Name | Description | Parameters |
|------------|-------------|------------|
| `video_play` | Video starts playing | video_title, video_id |
| `video_pause` | Video is paused | video_title, video_id |
| `video_complete` | Video finishes | video_title, video_id |
| `video_like` | User likes video | video_title, video_id |
| `video_comment` | User comments | video_title, video_id |
| `video_click` | User clicks video | video_title, video_id |
| `video_fullscreen_enter` | Enters fullscreen | video_title, video_id |
| `video_fullscreen_exit` | Exits fullscreen | video_title, video_id |

### Custom Events
You can add custom events anywhere in your templates:

```html
{% load analytics %}
<button onclick="gtag('event', 'custom_event', {'event_category': 'engagement', 'event_label': 'button_click'});">
    Click Me
</button>
```

## Troubleshooting

### Analytics Not Working
1. Check that `GOOGLE_ANALYTICS_ENABLED=True` in your environment
2. Verify your tracking ID is correct
3. Check browser console for JavaScript errors
4. Ensure the tracking code is loading in the page source

### Events Not Appearing
1. Check Google Analytics Real-time reports
2. Verify events are being triggered in browser console
3. Wait 24-48 hours for data to appear in standard reports

### Development vs Production
- Analytics is disabled when `GOOGLE_ANALYTICS_ENABLED=False`
- Use different tracking IDs for development and production
- Test with Real-time reports before deploying

## Advanced Configuration

### Enhanced Ecommerce (Optional)
If you plan to add ecommerce features, you can extend the tracking:

```html
{% google_analytics_event 'purchase' 'ecommerce' 'product_name' %}
```

### Custom Dimensions
You can add custom dimensions in Google Analytics and track them:

```javascript
gtag('event', 'custom_event', {
    'custom_parameter': 'value'
});
```

## Security Considerations

1. Never commit your `.env` file to version control
2. Use different tracking IDs for different environments
3. Consider implementing consent management for GDPR compliance
4. Regularly review and update your tracking implementation

## Support

For issues with this implementation, check:
1. Django logs for template errors
2. Browser console for JavaScript errors
3. Google Analytics Real-time reports for data flow
4. Google Analytics Help Center for GA4-specific issues

## Files Modified

- `adulto/settings.py` - Added GA configuration
- `core/templatetags/analytics.py` - Created template tags
- `templates/site/base.html` - Added tracking code
- `templates/site/video_detail.html` - Added video event tracking
- `templates/site/home.html` - Added video click tracking
- `requirements.txt` - Added python-dotenv dependency
- `.env.example` - Added environment variable examples
