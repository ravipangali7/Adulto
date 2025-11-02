from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
	"""Get an item from a dictionary using a key"""
	if dictionary and isinstance(dictionary, dict):
		return dictionary.get(key, '')
	return ''


@register.simple_tag
def get_ad_script(ads_dict, ad_id):
	"""Get ad script from ads dictionary by ad_id"""
	if ads_dict and isinstance(ads_dict, dict):
		return ads_dict.get(ad_id, '')
	return ''

