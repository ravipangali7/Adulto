from django import forms
import os
from .models import Category, Tag, Video, Comment, CMS, Settings, AgeVerification


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "category-slug"}),
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name", "slug"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tag name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "tag-slug"}),
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
            "video_file": forms.ClearableFileInput(attrs={"class": "form-control", "required": True}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "seo_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "SEO title"}),
            "seo_description": forms.TextInput(attrs={"class": "form-control", "placeholder": "SEO description"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make required fields explicit
        self.fields['title'].required = True
        self.fields['slug'].required = True
        
        # For edit forms, video_file is not required (existing file is kept)
        if self.instance and self.instance.pk:
            self.fields['video_file'].required = False
            self.fields['video_file'].help_text = "Leave empty to keep current video file"
        else:
            self.fields['video_file'].required = True
    
    def clean_video_file(self):
        video_file = self.cleaned_data.get('video_file')
        
        # For edit forms, if no new file is provided, keep the existing one
        if not video_file and self.instance and self.instance.pk and self.instance.video_file:
            return self.instance.video_file
        
        if video_file:
            # Check file size (500MB limit)
            max_size = 500 * 1024 * 1024  # 500MB in bytes
            if video_file.size > max_size:
                raise forms.ValidationError(f"File size too large. Maximum allowed size is 500MB. Your file is {video_file.size / (1024 * 1024):.1f}MB.")
            
            # Check file extension
            allowed_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
            file_extension = os.path.splitext(video_file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"Invalid file type. Allowed formats: {', '.join(allowed_extensions)}")
        
        return video_file
    
    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        slug = cleaned_data.get('slug')
        video_file = cleaned_data.get('video_file')
        
        # Additional validation
        if not title or not title.strip():
            raise forms.ValidationError("Title is required.")
        
        if not slug or not slug.strip():
            raise forms.ValidationError("Slug is required.")
        
        # For new videos, video file is required
        # For edit forms, either new file or existing file is required
        if not video_file and (not self.instance or not self.instance.pk or not self.instance.video_file):
            raise forms.ValidationError("Video file is required.")
        
        return cleaned_data


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
            "site_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Site name (e.g., Desi X Zone, xHamster)"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Modal title"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 10, "placeholder": "Modal content (HTML allowed)"}),
            "confirm_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "Confirm button text"}),
            "deny_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "Deny button text"}),
            "deny_redirect_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://www.google.com"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


