from django.contrib import admin
from .models import User, Category, Tag, Video, Settings, CMS, AgeVerification, Ad, DMCAReport


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("email", "name", "is_staff", "is_superuser", "is_freeze", "last_login")
	list_filter = ("is_staff", "is_superuser", "is_freeze")
	search_fields = ("email", "name")
	ordering = ("email",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "description", "image")
	search_fields = ("name", "slug", "description")
	prepopulated_fields = {"slug": ("name",)}
	list_editable = ("description",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ("name", "slug")
	search_fields = ("name", "slug")
	prepopulated_fields = {"slug": ("name",)}


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
	list_display = ("title", "uploader", "is_active", "has_thumbnail", "created_at")
	list_filter = ("is_active", "category", "tags", "created_at")
	search_fields = ("title", "slug", "description")
	prepopulated_fields = {"slug": ("title",)}
	filter_horizontal = ("tags", "category")
	list_editable = ("is_active",)
	actions = ["generate_thumbnails_action"]
	
	def has_thumbnail(self, obj):
		return bool(obj.thumbnail)
	has_thumbnail.boolean = True
	has_thumbnail.short_description = "Has Thumbnail"
	
	def generate_thumbnails_action(self, request, queryset):
		"""Generate thumbnails for selected videos"""
		success_count = 0
		error_count = 0
		
		for video in queryset:
			if video.video_file and not video.thumbnail:
				try:
					if video.generate_thumbnail():
						video.save(update_fields=['thumbnail'])
						success_count += 1
					else:
						error_count += 1
				except Exception as e:
					error_count += 1
					self.message_user(request, f"Error generating thumbnail for {video.title}: {e}", level='ERROR')
		
		if success_count > 0:
			self.message_user(request, f"Successfully generated {success_count} thumbnails", level='SUCCESS')
		if error_count > 0:
			self.message_user(request, f"Failed to generate {error_count} thumbnails", level='WARNING')
	
	generate_thumbnails_action.short_description = "Generate thumbnails for selected videos"


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
	list_display = ("key", "value", "description", "updated_at")
	search_fields = ("key", "value", "description")
	list_filter = ("created_at", "updated_at")
	readonly_fields = ("created_at", "updated_at")
	fieldsets = (
		(None, {
			'fields': ('key', 'value', 'description')
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)


@admin.register(CMS)
class CMSAdmin(admin.ModelAdmin):
	list_display = ("title", "slug", "in_navbar", "in_footer", "is_active", "updated_at")
	list_filter = ("in_navbar", "in_footer", "is_active", "created_at")
	search_fields = ("title", "slug", "content")
	prepopulated_fields = {"slug": ("title",)}
	list_editable = ("in_navbar", "in_footer", "is_active")
	readonly_fields = ("created_at", "updated_at")
	fieldsets = (
		(None, {
			'fields': ('title', 'slug', 'content')
		}),
		('Display Options', {
			'fields': ('in_navbar', 'in_footer', 'is_active')
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)


@admin.register(AgeVerification)
class AgeVerificationAdmin(admin.ModelAdmin):
	list_display = ("site_name", "title", "is_active", "updated_at")
	list_filter = ("is_active", "created_at")
	search_fields = ("site_name", "title", "content")
	list_editable = ("is_active",)
	readonly_fields = ("created_at", "updated_at")
	fieldsets = (
		(None, {
			'fields': ('site_name', 'title', 'content')
		}),
		('Button Settings', {
			'fields': ('confirm_text', 'deny_text', 'deny_redirect_url')
		}),
		('Status', {
			'fields': ('is_active',)
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
	list_display = ("placement", "get_placement_display", "ad_type", "get_ad_type_display", "is_active", "updated_at")
	list_filter = ("is_active", "placement", "ad_type", "created_at", "updated_at")
	search_fields = ("placement", "ad_type", "script")
	list_editable = ("is_active",)
	readonly_fields = ("placement", "ad_type", "created_at", "updated_at", "ad_placement_guide")
	
	fieldsets = (
		('Ad Configuration', {
			'fields': ('placement', 'ad_type', 'ad_placement_guide'),
			'description': 'Select placement location and ad format type. Same format can be used in multiple locations.'
		}),
		('Ad Content', {
			'fields': ('script', 'is_active'),
			'description': 'For instream-video and video-slider ad types, enter VAST tag URL (e.g., https://s.magsrv.com/v1/vast.php?idzone=XXXXXXX). For other types, paste HTML/JavaScript ad script.'
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)
	
	# Ad format guidelines - Type and Size recommendations for each format
	AD_GUIDELINES = {
		'banner': {
			'type': 'Banner Ad',
			'size': '728x90 (Desktop), 320x50 (Mobile), 300x250 (Rectangle)',
			'description': 'Standard banner ads. Most common ad format. Use in header, footer, sidebar, in-content areas. HIGH revenue.',
			'recommended': 'ExoClick Banner, TrafficJunky Banner, PropellerAds'
		},
		'sticky-banner': {
			'type': 'Sticky Banner',
			'size': '728x90 (Desktop), 320x50 (Mobile)',
			'description': 'Fixed position sticky banner that stays visible while scrolling. Always visible. HIGH priority.',
			'recommended': 'ExoClick Sticky Banner, TrafficJunky',
			'note': 'Available positions: top, bottom, left, right'
		},
		'fullpage-interstitial': {
			'type': 'Fullpage Interstitial',
			'size': 'Full Screen (Desktop & Mobile)',
			'description': 'Full-screen overlay ad triggered on internal link clicks. Can be closed by viewer. HIGH conversion rate.',
			'recommended': 'ExoClick Fullpage Interstitial, PopAds',
			'note': 'Place script in <head> or before </body>'
		},
		'instream-video': {
			'type': 'In-Stream Video Ad',
			'size': 'Video Format (VAST)',
			'description': 'Video ad that plays before/during/after main video. VERY HIGH priority - CPV based, high conversion.',
			'recommended': 'ExoClick In-Stream, VAST',
			'note': 'Works with all major video players (Video.js, etc.)'
		},
		'video-slider': {
			'type': 'Video Slider Ad',
			'size': '320x180 (Desktop), 280x160 (Mobile)',
			'description': 'Video slider that slides in and auto-plays. Fixed position bottom right. HIGH engagement.',
			'recommended': 'ExoClick Video Slider',
			'note': 'Customizable frequency capping'
		},
		'recommendation-widget': {
			'type': 'Recommendation Widget (Native Ads)',
			'size': 'Responsive Grid (Desktop/Mobile)',
			'description': 'Native ad widget that looks like content. HIGH CTR. Fully responsive.',
			'recommended': 'ExoClick Recommendation Widget',
			'note': 'Fully responsive - automatically adjusts for all screen sizes'
		},
		'multi-format': {
			'type': 'Multi-Format Ad',
			'size': 'Responsive (Auto-adapts)',
			'description': 'Ad that automatically adapts format based on available space and device. Smart optimization.',
			'recommended': 'ExoClick Multi-Format, PropellerAds',
			'note': 'Automatically selects best format for each placement'
		},
		'inpage-push-notifications': {
			'type': 'In-Page Push Notifications / Popunder',
			'size': 'Full Page / Notification Format',
			'description': 'Popunder ads or push notifications. Opens behind main window or as notification. HIGHEST conversion rate.',
			'recommended': 'ExoClick Popunder, PopAds, TrafficJunky',
			'note': 'Place script in <head> or before </body>. Works for desktop and mobile.'
		},
	}
	
	def ad_placement_guide(self, obj):
		"""Display ad format and size recommendations"""
		if not obj or not obj.ad_type:
			return '<div style="padding: 10px; background: #f0f0f0; border-left: 4px solid #007cba;"><strong>Select an ad format above to see guidelines.</strong></div>'

		guide = self.AD_GUIDELINES.get(obj.ad_type, {})
		if not guide:
			return '<div style="padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107;">No guidelines available for this ad format.</div>'
		
		html = f'''
		<div style="padding: 15px; background: #e7f3ff; border-left: 4px solid #007cba; margin-top: 10px;">
			<h4 style="margin-top: 0; color: #007cba;">📋 Ad Placement Guidelines</h4>
			<table style="width: 100%; border-collapse: collapse;">
				<tr>
					<td style="padding: 8px; font-weight: bold; width: 150px; vertical-align: top;">Ad Type:</td>
					<td style="padding: 8px; vertical-align: top;"><strong>{guide.get("type", "N/A")}</strong></td>
				</tr>
				<tr>
					<td style="padding: 8px; font-weight: bold; vertical-align: top;">Recommended Size:</td>
					<td style="padding: 8px; vertical-align: top;"><strong style="color: #d63384;">{guide.get("size", "N/A")}</strong></td>
				</tr>
				<tr>
					<td style="padding: 8px; font-weight: bold; vertical-align: top;">Description:</td>
					<td style="padding: 8px; vertical-align: top;">{guide.get("description", "N/A")}</td>
				</tr>
				<tr>
					<td style="padding: 8px; font-weight: bold; vertical-align: top;">Recommended Networks:</td>
					<td style="padding: 8px; vertical-align: top;">{guide.get("recommended", "N/A")}</td>
				</tr>
		'''
		
		if guide.get("note"):
			html += f'''
				<tr>
					<td style="padding: 8px; font-weight: bold; vertical-align: top;">Important Note:</td>
					<td style="padding: 8px; vertical-align: top; color: #856404; background: #fff3cd; border-left: 3px solid #ffc107;">
						⚠️ {guide.get("note")}
					</td>
				</tr>
			'''
		
		html += '''
			</table>
		</div>
		'''
		return html
	
	ad_placement_guide.short_description = 'Help & Guidelines'
	ad_placement_guide.allow_tags = True
	
	
	def get_readonly_fields(self, request, obj=None):
		"""Make placement and ad_type readonly after creation"""
		if obj:  # editing an existing object
			return self.readonly_fields
		else:  # creating a new object
			return ["ad_placement_guide"]  # Show guide even when creating
	
	def save_model(self, request, obj, form, change):
		"""Override save to ensure placement and ad_type are set correctly"""
		# Update script field help text for VAST URL ad types
		if obj.ad_type in ['instream-video', 'video-slider']:
			# Add note that script should be URL
			pass
		super().save_model(request, obj, form, change)


@admin.register(DMCAReport)
class DMCAReportAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'email', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
	list_filter = ('status', 'created_at', 'reviewed_at')
	search_fields = ('name', 'email', 'message', 'page_url')
	readonly_fields = ('created_at', 'updated_at')
	fieldsets = (
		('Reporter Information', {
			'fields': ('name', 'email')
		}),
		('Report Details', {
			'fields': ('message', 'page_url')
		}),
		('Status', {
			'fields': ('status', 'reviewed_by', 'reviewed_at')
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)
	
	def get_readonly_fields(self, request, obj=None):
		"""Make reviewed_by and reviewed_at readonly if not set"""
		readonly = list(self.readonly_fields)
		if obj and obj.reviewed_by:
			readonly.extend(['reviewed_by', 'reviewed_at'])
		return readonly
