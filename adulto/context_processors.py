from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q
from core.models import CMS, Settings, AgeVerification, Tag, Ad


def site_branding(request):
	return {
		"site_brand": getattr(settings, "SITE_BRAND", "Desi Sexy Videos"),
		"site_logo_url": getattr(settings, "SITE_LOGO_URL", "/static/logo.png"),
	}


def _fetch_cms_context_data():
	"""Build global CMS/settings context (one DB round-trip batch; cached)."""
	context = {}

	try:
		context['navbar_pages'] = list(
			CMS.objects.filter(in_navbar=True, is_active=True).order_by('title')
		)
	except Exception:
		context['navbar_pages'] = []

	try:
		context['footer_pages'] = list(
			CMS.objects.filter(in_footer=True, is_active=True).order_by('title')
		)
	except Exception:
		context['footer_pages'] = []

	defaults = {
		'site_title': 'Desi Sexy Videos',
		'site_description': 'Your premier destination for high-quality video content',
		'contact_email': '',
		'contact_phone': '',
		'social_facebook': '',
		'social_twitter': '',
		'social_instagram': '',
		'footer_text': 'Made with ❤️ for video lovers',
		'meta_verification_script': '',
	}
	try:
		settings_map = {
			row['key']: row['value']
			for row in Settings.objects.values('key', 'value')
		}
		for key, default in defaults.items():
			context[key] = settings_map.get(key, default)
	except Exception:
		context.update(defaults)

	try:
		context['age_verification'] = AgeVerification.get_active()
	except Exception:
		context['age_verification'] = None

	try:
		context['tags_count'] = Tag.objects.count()
		context['popular_tags'] = list(
			Tag.objects.annotate(
				videos_count=Count('videos', filter=Q(videos__is_active=True))
			)
			.filter(videos_count__gt=0)
			.order_by('-videos_count', 'name')[:10]
		)
	except Exception:
		context['popular_tags'] = []
		context['tags_count'] = 0

	try:
		all_ads = Ad.objects.all()
		active_ads_dict = {}
		ads_exist_dict = {}
		for ad in all_ads:
			composite_key = f"{ad.placement}-{ad.ad_type}"
			ads_exist_dict[composite_key] = True
			if ad.is_active:
				active_ads_dict[composite_key] = ad.get_ad_script()
		context['ads'] = active_ads_dict
		context['ads_exist'] = ads_exist_dict
	except Exception:
		context['ads'] = {}
		context['ads_exist'] = {}

	return context


def cms_and_settings(request):
	"""Context processor: CMS pages, settings, ads (cached 5 minutes)."""
	return cache.get_or_set('cms_context', _fetch_cms_context_data, 300)
