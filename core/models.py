from django.contrib.auth.models import AbstractUser
from django.db import models
import os
import cv2
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO


class User(AbstractUser):
	username = None
	first_name = None
	last_name = None
	
	name = models.CharField(max_length=150, blank=True)
	email = models.EmailField(unique=True)
	is_freeze = models.BooleanField(default=False)
	
	# Email activation fields
	is_email_verified = models.BooleanField(default=False)
	email_verification_token = models.CharField(max_length=100, blank=True, null=True)
	email_verification_created = models.DateTimeField(blank=True, null=True)
	
	# Override is_staff to be False by default until email is verified
	is_staff = models.BooleanField(default=False, help_text="Designates whether the user can log into the admin site. Only activated users can access admin.")

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	def __str__(self) -> str:
		return f'{self.email} -> {self.name}'
	
	def generate_email_verification_token(self):
		"""Generate a new email verification token"""
		import uuid
		from django.utils import timezone
		self.email_verification_token = str(uuid.uuid4())
		self.email_verification_created = timezone.now()
		self.save(update_fields=['email_verification_token', 'email_verification_created'])
		return self.email_verification_token
	
	def verify_email(self, token):
		"""Verify email with token"""
		if self.email_verification_token == token and self.email_verification_created:
			from django.utils import timezone
			from datetime import timedelta
			# Check if token is not expired (24 hours)
			if timezone.now() - self.email_verification_created < timedelta(hours=24):
				self.is_email_verified = True
				self.is_staff = True  # Activate user when email is verified
				self.email_verification_token = None
				self.email_verification_created = None
				self.save(update_fields=['is_email_verified', 'is_staff', 'email_verification_token', 'email_verification_created'])
				return True
		return False


class Category(models.Model):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True)
	description = models.TextField(blank=True, null=True, help_text="Category description for SEO")
	image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text="Optional category image")

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class Tag(models.Model):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True)
	description = models.TextField(blank=True, null=True, help_text="Tag description for SEO")

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class Video(models.Model):
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=220, unique=True)
	description = models.TextField(blank=True)
	uploader = models.ForeignKey('User', on_delete=models.CASCADE, related_name='videos')
	category = models.ManyToManyField(Category, related_name='videos', blank=True)
	tags = models.ManyToManyField(Tag, related_name='videos', blank=True)
	video_file = models.FileField(upload_to='videos/', blank=True, null=True)
	thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
	seo_title = models.CharField(max_length=255, blank=True)
	seo_description = models.TextField(blank=True)
	views = models.PositiveIntegerField(default=0)
	likes = models.PositiveIntegerField(default=0)
	duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
	is_active = models.BooleanField(default=True, help_text="If checked, video will be visible on the site")
	scheduled_publish_at = models.DateTimeField(blank=True, null=True, help_text="Schedule video to be published at this time")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return self.title

	def get_absolute_url(self):
		from django.urls import reverse
		return reverse('video_detail', args=[self.slug])

	def get_duration_display(self):
		"""Return formatted duration as MM:SS or HH:MM:SS"""
		if not self.duration:
			return "0:00"
		
		hours = self.duration // 3600
		minutes = (self.duration % 3600) // 60
		seconds = self.duration % 60
		
		if hours > 0:
			return f"{hours}:{minutes:02d}:{seconds:02d}"
		else:
			return f"{minutes}:{seconds:02d}"
	
	@property
	def is_scheduled(self):
		"""Check if video is scheduled for future publishing"""
		if not self.scheduled_publish_at:
			return False
		from django.utils import timezone
		return self.scheduled_publish_at > timezone.now()
	
	@property
	def is_draft(self):
		"""Check if video is in draft status (not active and not scheduled)"""
		return not self.is_active and not self.is_scheduled
	
	@property
	def status_display(self):
		"""Return human-readable status"""
		if self.is_active:
			return "Published"
		elif self.is_scheduled:
			return "Scheduled"
		else:
			return "Draft"

	def extract_duration(self):
		"""Extract duration from video file using OpenCV"""
		if not self.video_file:
			return False
		
		try:
			# Open video file
			video_path = self.video_file.path
			cap = cv2.VideoCapture(video_path)
			
			# Get video properties
			frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
			fps = cap.get(cv2.CAP_PROP_FPS)
			cap.release()
			
			if fps > 0:
				duration_seconds = int(frame_count / fps)
				self.duration = duration_seconds
				self.save(update_fields=['duration'])
				return True
			
		except Exception as e:
			print(f"Error extracting duration: {e}")
		
		return False

	def generate_thumbnail(self):
		"""Generate thumbnail from video file if no thumbnail exists"""
		if not self.video_file or self.thumbnail:
			return False
		
		try:
			# Open video file
			video_path = self.video_file.path
			cap = cv2.VideoCapture(video_path)
			
			# Get video properties
			frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
			fps = cap.get(cv2.CAP_PROP_FPS)
			
			# Calculate frame to extract (10% of video duration)
			frame_to_extract = int(frame_count * 0.1)
			cap.set(cv2.CAP_PROP_POS_FRAMES, frame_to_extract)
			
			# Read frame
			ret, frame = cap.read()
			cap.release()
			
			if not ret:
				return False
			
			# Convert BGR to RGB
			frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			
			# Convert to PIL Image
			pil_image = Image.fromarray(frame_rgb)
			
			# Resize to standard thumbnail size (320x180 for 16:9 aspect ratio)
			pil_image.thumbnail((320, 180), Image.Resampling.LANCZOS)
			
			# Save to BytesIO
			thumb_io = BytesIO()
			pil_image.save(thumb_io, format='JPEG', quality=85)
			thumb_io.seek(0)
			
			# Generate filename
			video_name = os.path.splitext(os.path.basename(self.video_file.name))[0]
			thumb_filename = f"{video_name}_thumb.jpg"
			
			# Save thumbnail
			self.thumbnail.save(
				thumb_filename,
				ContentFile(thumb_io.getvalue()),
				save=False
			)
			
			return True
			
		except Exception as e:
			print(f"Error generating thumbnail: {e}")
			return False

	def get_thumbnail_url(self):
		"""Get thumbnail URL if it exists"""
		if self.thumbnail:
			return self.thumbnail.url
		
		return None


class Comment(models.Model):
	video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
	guest_name = models.CharField(max_length=100, blank=True, help_text="Name for guest comments")
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_approved = models.BooleanField(default=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		author = self.user.name if self.user else self.guest_name or "Guest"
		return f'{author} - {self.video.title[:30]}...'
	
	@property
	def author_name(self):
		"""Return the name of the comment author (user or guest)"""
		return self.user.name if self.user else self.guest_name or "Guest"


class Settings(models.Model):
	"""Site settings that can be edited"""
	key = models.CharField(max_length=100, unique=True, help_text="Setting key (e.g., 'site_title', 'contact_email', 'meta_verification_script')")
	value = models.TextField(help_text="Setting value")
	description = models.TextField(blank=True, help_text="Description of what this setting does")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['key']
		verbose_name = "Setting"
		verbose_name_plural = "Settings"

	def __str__(self):
		return f"{self.key}: {self.value[:50]}..."

	@classmethod
	def get_setting(cls, key, default=None):
		"""Get a setting value by key"""
		try:
			return cls.objects.get(key=key).value
		except cls.DoesNotExist:
			return default

	@classmethod
	def set_setting(cls, key, value, description=""):
		"""Set a setting value by key"""
		setting, created = cls.objects.get_or_create(
			key=key,
			defaults={'value': value, 'description': description}
		)
		if not created:
			setting.value = value
			setting.description = description
			setting.save()
		return setting


class CMS(models.Model):
	"""Content Management System for pages"""
	title = models.CharField(max_length=200, help_text="Page title")
	slug = models.SlugField(max_length=220, unique=True, help_text="URL slug for the page")
	content = models.TextField(help_text="Page content (HTML allowed)")
	in_navbar = models.BooleanField(default=False, help_text="Show this page in the main navigation")
	in_footer = models.BooleanField(default=False, help_text="Show this page in the footer")
	is_active = models.BooleanField(default=True, help_text="Is this page active and visible?")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['title']
		verbose_name = "CMS Page"
		verbose_name_plural = "CMS Pages"

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		from django.urls import reverse
		return reverse('cms_page', args=[self.slug])


class AgeVerification(models.Model):
	"""Age verification modal content"""
	site_name = models.CharField(max_length=100, help_text="Name of the site (e.g., Adulto, xHamster)")
	title = models.CharField(max_length=200, help_text="Modal title")
	content = models.TextField(help_text="Modal content (HTML allowed)")
	confirm_text = models.CharField(max_length=100, default="I am 18 or older", help_text="Text for confirm button")
	deny_text = models.CharField(max_length=100, default="I am under 18", help_text="Text for deny button")
	deny_redirect_url = models.URLField(default="https://www.google.com", help_text="URL to redirect to when user denies age")
	is_active = models.BooleanField(default=True, help_text="Show this modal on the site")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Age Verification"
		verbose_name_plural = "Age Verification"

	def __str__(self):
		return f"Age Verification - {self.site_name}"

	@classmethod
	def get_active(cls):
		"""Get the active age verification modal"""
		try:
			return cls.objects.filter(is_active=True).first()
		except:
			return None


# Ad Type Choices - Format Only (8 total formats)
AD_TYPE_CHOICES = [
	('banner', 'Banner'),
	('sticky-banner', 'Sticky Banner'),
	('fullpage-interstitial', 'Fullpage Interstitial'),
	('instream-video', 'In-Stream Video'),
	('video-slider', 'Video Slider'),
	('recommendation-widget', 'Recommendation Widget'),
	('multi-format', 'Multi-Format'),
	('inpage-push-notifications', 'In-Page Push Notifications'),
]

# Placement Choices - Strategic locations only (13 total)
PLACEMENT_CHOICES = [
	# Global (All Pages)
	('header-top', 'Header Top Banner (728x90 Desktop, 320x50 Mobile)'),
	('global-sticky-bottom', 'Global Sticky Banner Bottom (728x90 Desktop, 320x50 Mobile)'),
	('global-popunder-desktop', 'Global Popunder Desktop (Full Page)'),
	('global-popunder-mobile', 'Global Popunder Mobile (Full Page)'),
	('global-interstitial', 'Global Interstitial (Full Screen Desktop/Mobile)'),
	('global-instant-message', 'Global Instant Message Chat (300x250 Desktop, 280x250 Mobile)'),
	('global-inpage-push', 'Global In-Page Push Notification (Responsive, Configurable Position)'),
	
	# Reusable Placements (Multiple Pages)
	('incontent', 'In-Content Banner (728x90 Desktop, Full Width Mobile) - Home/Videos/Search'),
	('sidebar', 'Sidebar Rectangle (300x250 Desktop, Full Width Mobile) - All Pages with Sidebar'),
	
	# Page-Specific (Unique)
	('home-bottom', 'Home Bottom Leaderboard (970x250 Desktop, 728x90 Mobile)'),
	('video-below-player', 'Video Below Player Banner (728x90 Desktop, 320x50 Mobile)'),
	('video-instream', 'Video In-Stream VAST (VAST URL for instream-video ad_type)'),
	('video-slider', 'Video Slider (VAST URL, slides from right bottom)'),
]


class Ad(models.Model):
	"""Dynamic ad management - format-based ad types with strategic placements"""
	placement = models.CharField(
		max_length=50,
		choices=PLACEMENT_CHOICES,
		help_text="Select the ad placement location"
	)
	ad_type = models.CharField(
		max_length=50,
		choices=AD_TYPE_CHOICES,
		help_text="Select the ad format type (banner, sticky-banner, etc.)"
	)
	script = models.TextField(help_text="HTML/JavaScript ad script content (or VAST URL for instream-video/video-slider)")
	is_active = models.BooleanField(default=True, help_text="Enable/disable this ad")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['placement', 'ad_type']
		verbose_name = "Ad"
		verbose_name_plural = "Ads"
		unique_together = [['placement', 'ad_type']]  # One ad per placement+format combo

	def __str__(self):
		return f"{self.get_placement_display()} - {self.get_ad_type_display()} ({'Active' if self.is_active else 'Inactive'})"

	def get_ad_script(self):
		"""Return ad script if active, else None"""
		if self.is_active and self.script:
			return self.script
		return None

	@classmethod
	def get_ad_by_placement_and_type(cls, placement, ad_type):
		"""Get active ad by placement and ad_type"""
		try:
			return cls.objects.get(placement=placement, ad_type=ad_type, is_active=True)
		except cls.DoesNotExist:
			return None
