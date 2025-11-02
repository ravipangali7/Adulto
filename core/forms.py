from django import forms
import os
from .models import Category, Tag, Video, Comment, CMS, Settings, AgeVerification, Ad


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "category-slug"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Category description for SEO"}),
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name", "slug", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tag name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "tag-slug"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Tag description for SEO"}),
        }


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        exclude = ["uploader", "created_at", "views", "likes", "duration"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Video title", "required": True}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "video-slug", "required": True}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Description"}),
            "category": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "tags": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "video_file": forms.ClearableFileInput(attrs={"class": "form-control", "required": True, "accept": "video/mp4"}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/jpeg,image/jpg"}),
            "seo_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "SEO title"}),
            "seo_description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "SEO description"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "scheduled_publish_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make required fields explicit
        self.fields['title'].required = True
        self.fields['slug'].required = True
        
        # Add custom fields for publishing options
        self.fields['publish_option'] = forms.ChoiceField(
            choices=[
                ('publish_now', 'Publish Now'),
                ('draft', 'Save as Draft'),
                ('schedule', 'Schedule for Later')
            ],
            widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
            initial='publish_now'
        )
        
        # For edit forms, video_file is not required (existing file is kept)
        if self.instance and self.instance.pk:
            self.fields['video_file'].required = False
            self.fields['video_file'].help_text = "Leave empty to keep current video file"
            # Remove required attribute from widget for edit forms
            self.fields['video_file'].widget.attrs.pop('required', None)
            
            # Set initial publish option based on current state
            if self.instance.is_active:
                self.fields['publish_option'].initial = 'publish_now'
            elif self.instance.scheduled_publish_at:
                self.fields['publish_option'].initial = 'schedule'
            else:
                self.fields['publish_option'].initial = 'draft'
        else:
            self.fields['video_file'].required = True
        
        # Make scheduled_publish_at not required initially
        self.fields['scheduled_publish_at'].required = False
        
        # Convert scheduled_publish_at to Nepal timezone for display
        if self.instance and self.instance.pk and self.instance.scheduled_publish_at:
            import pytz
            from django.utils import timezone
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            utc_time = self.instance.scheduled_publish_at
            if utc_time.tzinfo is None:
                utc_time = timezone.make_aware(utc_time)
            nepal_time = utc_time.astimezone(nepal_tz)
            # Format for datetime-local input (YYYY-MM-DDTHH:MM)
            self.fields['scheduled_publish_at'].initial = nepal_time.strftime('%Y-%m-%dT%H:%M')
    
    def clean_video_file(self):
        video_file = self.cleaned_data.get('video_file')
        
        # For edit forms, if no new file is provided, keep the existing one
        if not video_file and self.instance and self.instance.pk and self.instance.video_file:
            # Check if the existing file actually exists
            if hasattr(self.instance.video_file, 'path') and os.path.exists(self.instance.video_file.path):
                return self.instance.video_file
            else:
                # If file doesn't exist, return None to indicate no file
                return None
        
        if video_file:
            # Check file size (300MB limit)
            max_size = 300 * 1024 * 1024  # 300MB in bytes
            if video_file.size > max_size:
                raise forms.ValidationError(f"File size too large. Maximum allowed size is 300MB. Your file is {video_file.size / (1024 * 1024):.1f}MB.")
            
            # Check file extension - only MP4 allowed
            allowed_extensions = ['.mp4']
            file_extension = os.path.splitext(video_file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"Invalid file type. Only MP4 format is allowed.")
        
        return video_file
    
    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get('thumbnail')
        
        if thumbnail:
            # Check file extension - only JPG allowed
            allowed_extensions = ['.jpg', '.jpeg']
            file_extension = os.path.splitext(thumbnail.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"Invalid thumbnail format. Only JPG/JPEG format is allowed.")
        
        return thumbnail
    
    def clean(self):
        cleaned_data = super().clean()
        publish_option = cleaned_data.get('publish_option')
        scheduled_publish_at = cleaned_data.get('scheduled_publish_at')
        
        # Validate scheduling
        if publish_option == 'schedule':
            if not scheduled_publish_at:
                raise forms.ValidationError("Please select a date and time for scheduling.")
            
            # Convert Nepal time to UTC for storage
            import pytz
            from django.utils import timezone
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            
            # If scheduled_publish_at is naive, assume it's Nepal time
            if scheduled_publish_at.tzinfo is None:
                # Make it timezone-aware as Nepal time
                nepal_time = nepal_tz.localize(scheduled_publish_at)
                # Convert to UTC
                utc_time = nepal_time.astimezone(pytz.UTC)
                cleaned_data['scheduled_publish_at'] = utc_time
            
            # Check if the converted time is in the future
            if cleaned_data['scheduled_publish_at'] <= timezone.now():
                raise forms.ValidationError("Scheduled time must be in the future.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        publish_option = self.cleaned_data.get('publish_option')
        
        # Generate unique slug if not provided or if it's a new instance
        if not instance.slug or not instance.pk:
            from django.utils.text import slugify
            base_slug = slugify(instance.title)
            slug = base_slug
            
            # Ensure slug is unique
            counter = 1
            while instance.__class__.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            instance.slug = slug
        
        # Handle publishing options
        if publish_option == 'publish_now':
            instance.is_active = True
            instance.scheduled_publish_at = None
        elif publish_option == 'draft':
            instance.is_active = False
            instance.scheduled_publish_at = None
        elif publish_option == 'schedule':
            instance.is_active = False
            instance.scheduled_publish_at = self.cleaned_data.get('scheduled_publish_at')
        
        if commit:
            instance.save()
            self.save_m2m()
            
            # Video scheduling is handled automatically by the background scheduler
            # No need to manually schedule - the scheduler will check every 30 seconds
        
        return instance


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'guest_name']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment...',
                'required': True
            }),
            'guest_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your name (optional)',
                'maxlength': 100
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If user is authenticated, hide guest_name field
        if self.user and self.user.is_authenticated:
            self.fields['guest_name'].widget = forms.HiddenInput()
            self.fields['guest_name'].required = False
        else:
            # For guest users, make guest_name required
            self.fields['guest_name'].required = True
            self.fields['guest_name'].widget.attrs['required'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        guest_name = cleaned_data.get('guest_name')
        
        # Validate content
        if not content or not content.strip():
            raise forms.ValidationError("Comment content is required.")
        
        # For guest users, validate guest_name
        if not self.user or not self.user.is_authenticated:
            if not guest_name or not guest_name.strip():
                raise forms.ValidationError("Name is required for guest comments.")
            # Clean and limit guest name
            cleaned_data['guest_name'] = guest_name.strip()[:100]
        
        return cleaned_data
    
    def save(self, commit=True):
        comment = super().save(commit=False)
        if self.user and self.user.is_authenticated:
            comment.user = self.user
            comment.guest_name = ''
        else:
            comment.user = None
        if commit:
            comment.save()
        return comment


class CMSForm(forms.ModelForm):
    class Meta:
        model = CMS
        fields = ["title", "slug", "content", "in_navbar", "in_footer", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Page title"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "page-slug"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 10, "placeholder": "Page content (HTML allowed)"}),
            "in_navbar": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "in_footer": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ["key", "value", "description"]
        widgets = {
            "key": forms.TextInput(attrs={"class": "form-control", "placeholder": "setting_key"}),
            "value": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Setting value"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Description of what this setting does"}),
        }


class AgeVerificationForm(forms.ModelForm):
    class Meta:
        model = AgeVerification
        fields = ["site_name", "title", "content", "confirm_text", "deny_text", "deny_redirect_url", "is_active"]
        widgets = {
            "site_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Site name (e.g., Desi Sexy Videos, xHamster)"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Modal title"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 10, "placeholder": "Modal content (HTML allowed)"}),
            "confirm_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "Confirm button text"}),
            "deny_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "Deny button text"}),
            "deny_redirect_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://www.google.com"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ["placement", "ad_type", "script", "is_active"]
        widgets = {
            "placement": forms.Select(attrs={"class": "form-control"}),
            "ad_type": forms.Select(attrs={"class": "form-control"}),
            "script": forms.Textarea(attrs={"class": "form-control", "rows": 15, "placeholder": "Paste your ad script here (HTML/JavaScript) or VAST URL"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing existing ad, make placement and ad_type readonly/disabled
        if self.instance and self.instance.pk:
            self.fields['placement'].widget.attrs['disabled'] = True
            self.fields['ad_type'].widget.attrs['disabled'] = True
            self.fields['placement'].help_text = "Placement cannot be changed after creation. Delete and create new one to change."
            self.fields['ad_type'].help_text = "Ad type cannot be changed after creation. Delete and create new one to change."
            # Store original values for when fields are disabled
            self.fields['placement'].widget.attrs['data-original-value'] = self.instance.placement
            self.fields['ad_type'].widget.attrs['data-original-value'] = self.instance.ad_type
        
        # Update help text based on ad_type for script field
        if self.instance and self.instance.pk and self.instance.ad_type in ['instream-video', 'video-slider']:
            self.fields['script'].help_text = "Enter VAST tag URL (e.g., https://s.magsrv.com/v1/vast.php?idzone=XXXXXXX). This URL will be used by video player."
            self.fields['script'].widget.attrs['placeholder'] = "Enter VAST tag URL here..."
        elif 'ad_type' in self.initial and self.initial['ad_type'] in ['instream-video', 'video-slider']:
            self.fields['script'].help_text = "Enter VAST tag URL (e.g., https://s.magsrv.com/v1/vast.php?idzone=XXXXXXX). This URL will be used by video player."
            self.fields['script'].widget.attrs['placeholder'] = "Enter VAST tag URL here..."
    
    def clean_placement(self):
        """Handle disabled placement field when editing"""
        if self.instance and self.instance.pk:
            if 'placement' not in self.cleaned_data:
                return self.instance.placement
            return self.cleaned_data.get('placement')
        return self.cleaned_data.get('placement')
    
    def clean_ad_type(self):
        """Handle disabled ad_type field when editing"""
        if self.instance and self.instance.pk:
            if 'ad_type' not in self.cleaned_data:
                return self.instance.ad_type
            return self.cleaned_data.get('ad_type')
        return self.cleaned_data.get('ad_type')
    
    def clean_script(self):
        """Validate script field - if instream-video or video-slider, must be valid URL"""
        script = self.cleaned_data.get('script', '').strip()
        ad_type = self.cleaned_data.get('ad_type') or (self.instance.ad_type if self.instance and self.instance.pk else None)
        
        if ad_type in ['instream-video', 'video-slider']:
            # For VAST URL ad types, validate that script is a valid URL
            from django.core.validators import URLValidator
            from django.core.exceptions import ValidationError
            
            if not script:
                raise forms.ValidationError("VAST tag URL is required for this ad type.")
            
            try:
                validator = URLValidator()
                validator(script)
            except ValidationError:
                raise forms.ValidationError("Please enter a valid VAST tag URL (e.g., https://s.magsrv.com/v1/vast.php?idzone=XXXXXXX).")
        
        return script
    
    def clean(self):
        """Override clean to ensure placement and ad_type are set when editing"""
        cleaned_data = super().clean()
        # If editing and fields are missing (disabled fields), restore them
        if self.instance and self.instance.pk:
            if 'placement' not in cleaned_data:
                cleaned_data['placement'] = self.instance.placement
            if 'ad_type' not in cleaned_data:
                cleaned_data['ad_type'] = self.instance.ad_type
        return cleaned_data


