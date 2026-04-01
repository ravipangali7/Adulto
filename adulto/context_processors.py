from django.conf import settings
from django.db import models
from core.models import CMS, Settings, AgeVerification, Tag, Ad


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
	
	try:
		# Get all ads (both active and inactive) to check existence
		all_ads = Ad.objects.all()
		active_ads_dict = {}
		ads_exist_dict = {}

		for ad in all_ads:
			# Create composite key: {placement}-{ad_type} (e.g., "header-top-banner")
			composite_key = f"{ad.placement}-{ad.ad_type}"
			ads_exist_dict[composite_key] = True  # Track that ad exists
			ads_exist_dict[ad.placement] = True
			if ad.ad_type == 'banner':
				ads_exist_dict[f"{ad.placement}-banner"] = True
			if ad.is_active:
				ad_script = ad.get_ad_script()
				active_ads_dict[composite_key] = ad_script
				active_ads_dict[ad.placement] = ad_script
				if ad.ad_type == 'banner':
					active_ads_dict[f"{ad.placement}-banner"] = ad_script

		context['ads'] = active_ads_dict  # Only active ads with scripts (keyed by composite)
		context['ads_exist'] = ads_exist_dict  # Track which ads exist (active or inactive)

		# Home-only dedupe map: keep first slot when the same script is reused.
		home_slot_order = [
			'header-top',
			'incontent',
			'video-below-player',
			'sidebar',
			'video-sidebar',
			'home-bottom',
		]
		seen_home_signatures = set()
		home_ad_slot_enabled = {}
		for slot_id in home_slot_order:
			ad_script = active_ads_dict.get(slot_id, '')
			if ad_script:
				signature = ad_script.strip()
				if signature in seen_home_signatures:
					home_ad_slot_enabled[slot_id] = False
				else:
					seen_home_signatures.add(signature)
					home_ad_slot_enabled[slot_id] = True
			else:
				# Keep enabled; partial will still hide missing/inactive ads.
				home_ad_slot_enabled[slot_id] = True
		context['home_ad_slot_enabled'] = home_ad_slot_enabled
	except Exception as e:
		print(f"Error getting ads: {e}")
		context['ads'] = {}
		context['ads_exist'] = {}
		context['home_ad_slot_enabled'] = {}
	
	try:
		# Get meta verification script from Settings
		meta_verification = Settings.get_setting('meta_verification_script', '')
		context['meta_verification_script'] = meta_verification
	except Exception as e:
		print(f"Error getting meta verification script: {e}")
		context['meta_verification_script'] = ''
	
	return context


