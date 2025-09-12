from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def google_analytics():
    """
    Returns Google Analytics tracking code if enabled and tracking ID is provided.
    """
    if not settings.GOOGLE_ANALYTICS_ENABLED or not settings.GOOGLE_ANALYTICS_TRACKING_ID:
        return ''
    
    tracking_id = settings.GOOGLE_ANALYTICS_TRACKING_ID
    
    # Google Analytics 4 (GA4) tracking code
    ga_code = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={tracking_id}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{tracking_id}', {{
            'page_title': document.title,
            'page_location': window.location.href
        }});
    </script>
    """
    
    return mark_safe(ga_code)

@register.simple_tag
def google_analytics_event(event_name, event_category=None, event_label=None, value=None):
    """
    Returns Google Analytics event tracking code.
    Usage: {% google_analytics_event 'video_play' 'engagement' 'video_title' %}
    """
    if not settings.GOOGLE_ANALYTICS_ENABLED or not settings.GOOGLE_ANALYTICS_TRACKING_ID:
        return ''
    
    event_params = {
        'event_name': event_name
    }
    
    if event_category:
        event_params['event_category'] = event_category
    if event_label:
        event_params['event_label'] = event_label
    if value:
        event_params['value'] = value
    
    # Convert to JavaScript object
    params_str = ', '.join([f"'{k}': '{v}'" for k, v in event_params.items()])
    
    event_code = f"""
    <script>
        gtag('event', '{event_name}', {{{params_str}}});
    </script>
    """
    
    return mark_safe(event_code)

@register.simple_tag
def google_analytics_page_view(page_title=None, page_location=None):
    """
    Manually trigger a page view event.
    """
    if not settings.GOOGLE_ANALYTICS_ENABLED or not settings.GOOGLE_ANALYTICS_TRACKING_ID:
        return ''
    
    params = {}
    if page_title:
        params['page_title'] = page_title
    if page_location:
        params['page_location'] = page_location
    
    params_str = ', '.join([f"'{k}': '{v}'" for k, v in params.items()])
    
    page_view_code = f"""
    <script>
        gtag('event', 'page_view', {{{params_str}}});
    </script>
    """
    
    return mark_safe(page_view_code)
