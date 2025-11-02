from django.core.management.base import BaseCommand
from core.models import Ad, AD_TYPE_CHOICES, PLACEMENT_CHOICES


class Command(BaseCommand):
	help = 'Create default inactive ads for all ad types with demo scripts'

	def handle(self, *args, **options):
		created_count = 0
		skipped_count = 0
		updated_count = 0

		# Demo script templates for each ad format type
		demo_scripts = {
			'banner': '''<script async type="application/javascript" src="https://a.magsrv.com/ad-provider.js"></script>
<ins class="eas6a97888e2" data-zoneid="YOUR_ZONE_ID"></ins>
<script>(AdProvider = window.AdProvider || []).push({"serve": {}});</script>''',
			
			'sticky-banner': '''<script async type="application/javascript" src="https://a.magsrv.com/ad-provider.js"></script>
<ins class="eas6a97888e2" data-zoneid="YOUR_ZONE_ID"></ins>
<script>(AdProvider = window.AdProvider || []).push({"serve": {}});</script>''',
			
			'fullpage-interstitial': '''<!-- Fullpage Interstitial Ad Script - HIGH REVENUE -->
<script type="text/javascript">
// Replace with your interstitial script (ExoClick, PopAds)
console.log("Interstitial ad - Replace with actual script");
</script>''',
			
			'instream-video': 'https://s.magsrv.com/v1/vast.php?idzone=YOUR_ZONE_ID',  # VAST URL, not script
			
			'video-slider': 'https://s.magsrv.com/v1/vast.php?idzone=YOUR_ZONE_ID',  # VAST URL, not script
			
			'recommendation-widget': '''<!-- Recommendation Widget/Native Ad Script -->
<script type="text/javascript">
// Replace with your recommendation widget script
console.log("Recommendation widget - Replace with actual script");
</script>''',
			
			'multi-format': '''<!-- Multi-Format Ad Script -->
<script async type="application/javascript" src="https://a.magsrv.com/ad-provider.js"></script>
<ins class="eas6a97888e2" data-zoneid="YOUR_ZONE_ID"></ins>
<script>(AdProvider = window.AdProvider || []).push({"serve": {}});</script>''',
			
			'inpage-push-notifications': '''<!-- In-Page Push Notifications Ad Script -->
<script type="text/javascript">
// Replace with your popunder/instant message script (ExoClick, PopAds, TrafficJunky)
console.log("In-page push notification ad - Replace with actual script");
</script>'''
		}

		# Get demo script by ad_type format
		def get_demo_script(ad_type):
			return demo_scripts.get(ad_type, demo_scripts['banner'])  # Default to banner

		# Define strategic placement+format combinations
		# Only create ads for sensible combinations
		strategic_combinations = [
			# Global placements
			('header-top', 'banner'),
			('global-sticky-bottom', 'sticky-banner'),
			('global-popunder-desktop', 'inpage-push-notifications'),
			('global-popunder-mobile', 'inpage-push-notifications'),
			('global-interstitial', 'fullpage-interstitial'),
			('global-instant-message', 'inpage-push-notifications'),
			('global-inpage-push', 'inpage-push-notifications'),
			
			# Reusable placements
			('incontent', 'banner'),
			('sidebar', 'banner'),
			
			# Page-specific
			('home-bottom', 'banner'),
			('video-below-player', 'banner'),
			('video-sidebar', 'banner'),
			('video-instream', 'instream-video'),  # Special: VAST URL
			('video-slider', 'video-slider'),  # Special: VAST URL
		]

		# Create ads for strategic combinations
		for placement_value, ad_type_value in strategic_combinations:
			ad, created = Ad.objects.get_or_create(
				placement=placement_value,
				ad_type=ad_type_value,
				defaults={
					'script': get_demo_script(ad_type_value),
					'is_active': False,  # All default ads are inactive
				}
			)

			if created:
				created_count += 1
				placement_display = dict(PLACEMENT_CHOICES).get(placement_value, placement_value)
				ad_type_display = dict(AD_TYPE_CHOICES).get(ad_type_value, ad_type_value)
				self.stdout.write(
					self.style.SUCCESS(
						f'✓ Created: {placement_display} - {ad_type_display}'
					)
				)
			else:
				# Ad already exists - update script if it's the default demo
				if 'YOUR_ZONE_ID' in ad.script or 'Replace with' in ad.script or 'console.log' in ad.script:
					ad.script = get_demo_script(ad_type_value)
					ad.is_active = False  # Ensure it's inactive
					ad.save()
					updated_count += 1
					placement_display = dict(PLACEMENT_CHOICES).get(placement_value, placement_value)
					ad_type_display = dict(AD_TYPE_CHOICES).get(ad_type_value, ad_type_value)
					self.stdout.write(
						self.style.WARNING(
							f'↻ Updated: {placement_display} - {ad_type_display}'
						)
					)
				else:
					skipped_count += 1
					placement_display = dict(PLACEMENT_CHOICES).get(placement_value, placement_value)
					ad_type_display = dict(AD_TYPE_CHOICES).get(ad_type_value, ad_type_value)
					self.stdout.write(
						self.style.NOTICE(
							f'⊘ Skipped: {placement_display} - {ad_type_display} - Already has custom script'
						)
					)

		# Summary
		self.stdout.write('')
		self.stdout.write(self.style.SUCCESS('=' * 60))
		self.stdout.write(self.style.SUCCESS('Default Ads Creation Summary'))
		self.stdout.write(self.style.SUCCESS('=' * 60))
		self.stdout.write(
			self.style.SUCCESS(f'✓ Created: {created_count} new ads')
		)
		if updated_count > 0:
			self.stdout.write(
				self.style.WARNING(f'↻ Updated: {updated_count} existing ads')
			)
		if skipped_count > 0:
			self.stdout.write(
				self.style.NOTICE(f'⊘ Skipped: {skipped_count} ads (already have custom scripts)')
			)
		self.stdout.write('')
		self.stdout.write(
			self.style.SUCCESS(
				f'Total: {len(strategic_combinations)} strategic ad placements created'
			)
		)
		self.stdout.write('')
		self.stdout.write(
			self.style.WARNING(
				'Note: All created ads are INACTIVE by default. '
				'Go to Ad Management to activate them and update with your actual ad scripts.'
			)
		)

