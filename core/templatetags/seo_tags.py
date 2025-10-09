from django import template
from django.utils.safestring import mark_safe
import json
import os

register = template.Library()


@register.simple_tag
def breadcrumb_json(breadcrumbs):
    """
    Generate JSON-LD breadcrumb structured data
    """
    if not breadcrumbs:
        return ""
    
    breadcrumb_list = []
    for i, (name, url) in enumerate(breadcrumbs, 1):
        breadcrumb_list.append({
            "@type": "ListItem",
            "position": i,
            "name": name,
            "item": url
        })
    
    structured_data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumb_list
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(structured_data)}</script>')


@register.simple_tag
def generate_meta_keywords(video=None, categories=None, tags=None):
    """
    Generate dynamic meta keywords based on content
    """
    keywords = []
    
    if video:
        if video.tags.exists():
            keywords.extend([tag.name for tag in video.tags.all()])
        if video.category.exists():
            keywords.extend([cat.name for cat in video.category.all()])
        keywords.append('video')
        keywords.append('streaming')
    
    if categories:
        keywords.extend([cat.name for cat in categories])
    
    if tags:
        keywords.extend([tag.name for tag in tags])
    
    # Add general keywords
    keywords.extend(['entertainment', 'online videos', 'video platform'])
    
    # Remove duplicates and join
    return ', '.join(list(set(keywords)))


@register.simple_tag
def generate_meta_description(content, max_length=160):
    """
    Generate meta description from content
    """
    if not content:
        return "Discover and watch amazing videos across various categories. Your premier destination for high-quality video content."
    
    # Clean content
    import re
    clean_content = re.sub(r'<[^>]+>', '', str(content))  # Remove HTML tags
    clean_content = re.sub(r'\s+', ' ', clean_content)  # Normalize whitespace
    
    if len(clean_content) <= max_length:
        return clean_content
    
    # Truncate at word boundary
    truncated = clean_content[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:  # Only truncate at word if it's not too short
        truncated = truncated[:last_space]
    
    return truncated + "..."


@register.filter
def basename(value):
    """
    Extract filename from file path
    """
    if not value:
        return ""
    return os.path.basename(str(value))
