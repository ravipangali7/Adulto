from django.conf import settings
from django.db import models
from core.models import CMS, Settings, AgeVerification, Tag


def site_branding(request):
	return {
		"site_brand": getattr(settings, "SITE_BRAND", "Desi Sexy Videos"),
		"site_logo_url": getattr(settings, "SITE_LOGO_URL", "/static/logo.png"),
	}


def cms_and_settings(request):
	"""Context processor to make CMS pages and settings available globally"""
	context = {}
	
	try:
		# Get CMS pages for navbar
		navbar_pages = CMS.objects.filter(in_navbar=True, is_active=True).order_by('title')
		context['navbar_pages'] = navbar_pages
	except:
		context['navbar_pages'] = []
	
	try:
		# Get CMS pages for footer
		footer_pages = CMS.objects.filter(in_footer=True, is_active=True).order_by('title')
		context['footer_pages'] = footer_pages
	except:
		context['footer_pages'] = []
	
	try:
		# Get common settings
		context['site_title'] = Settings.get_setting('site_title', 'Desi Sexy Videos')
		context['site_description'] = Settings.get_setting('site_description', 'Your premier destination for high-quality video content')
		context['contact_email'] = Settings.get_setting('contact_email', '')
		context['contact_phone'] = Settings.get_setting('contact_phone', '')
		context['social_facebook'] = Settings.get_setting('social_facebook', '')
		context['social_twitter'] = Settings.get_setting('social_twitter', '')
		context['social_instagram'] = Settings.get_setting('social_instagram', '')
		context['footer_text'] = Settings.get_setting('footer_text', 'Made with ❤️ for video lovers')
	except:
		# Fallback values if settings don't exist
		context.update({
			'site_title': 'Desi Sexy Videos',
			'site_description': 'Your premier destination for high-quality video content',
			'contact_email': '',
			'contact_phone': '',
			'social_facebook': '',
			'social_twitter': '',
			'social_instagram': '',
			'footer_text': 'Made with ❤️ for video lovers'
		})
	
	try:
		# Get active age verification modal
		age_verification = AgeVerification.get_active()
		context['age_verification'] = age_verification
	except:
		context['age_verification'] = None
	
	try:
		# Get popular tags for sub-navbar (top 10 most used tags)
		# First try to get tags with videos, if none exist, get all tags
		
		# If no tags have videos, just get the first 10 tags
		popular_tags = Tag.objects.all()
		
		context['popular_tags'] = popular_tags
		context['tags_count'] = Tag.objects.count()
		
	except Exception as e:
		print(f"Error getting tags: {e}")
		context['popular_tags'] = []
		context['tags_count'] = 0
	
	return context


