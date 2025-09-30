from django.contrib import admin
from .models import User, Category, Tag, Video, Settings, CMS, AgeVerification


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
