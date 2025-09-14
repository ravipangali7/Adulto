from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Category, Tag, Video, CMS, Settings, AgeVerification, User, Comment
from .forms import CategoryForm, TagForm, VideoForm, CMSForm, SettingsForm, AgeVerificationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login


def login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'site/login.html')
    else:
        return render(request, 'site/login.html')



# Create your views here.
@login_required(login_url='login')
def dashboard(request):
	from django.db.models import Sum, Count, Avg
	from django.utils import timezone
	from datetime import timedelta
	
	# Get dashboard statistics
	total_videos = Video.objects.count()
	total_categories = Category.objects.count()
	total_tags = Tag.objects.count()
	
	# Get analytics data
	total_views = Video.objects.aggregate(total=Sum('views'))['total'] or 0
	total_likes = Video.objects.aggregate(total=Sum('likes'))['total'] or 0
	total_comments = Comment.objects.count()
	
	# Calculate averages
	avg_views_per_video = round(total_views / total_videos, 0) if total_videos > 0 else 0
	avg_likes_per_video = round(total_likes / total_videos, 0) if total_videos > 0 else 0
	
	# Get recent videos with engagement data
	recent_videos = Video.objects.select_related('uploader').prefetch_related('category', 'tags', 'comments').order_by('-created_at')[:5]
	
	# Get most liked videos
	most_liked_videos = Video.objects.select_related('uploader').prefetch_related('category', 'tags', 'comments').order_by('-likes')[:5]
	
	# Get most viewed videos
	most_viewed_videos = Video.objects.select_related('uploader').prefetch_related('category', 'tags', 'comments').order_by('-views')[:5]
	
	# Get recent comments
	recent_comments = Comment.objects.select_related('video', 'user').order_by('-created_at')[:5]
	
	# Get videos by category with engagement data
	videos_by_category = []
	for category in Category.objects.all():
		videos_in_category = category.videos.all()
		count = videos_in_category.count()
		if count > 0:
			total_views_in_category = videos_in_category.aggregate(total=Sum('views'))['total'] or 0
			total_likes_in_category = videos_in_category.aggregate(total=Sum('likes'))['total'] or 0
			videos_by_category.append({
				'name': category.name,
				'count': count,
				'total_views': total_views_in_category,
				'total_likes': total_likes_in_category
			})
	
	# Get recent activity (last 7 days)
	week_ago = timezone.now() - timedelta(days=7)
	recent_uploads = Video.objects.filter(created_at__gte=week_ago).count()
	recent_views = Video.objects.filter(created_at__gte=week_ago).aggregate(total=Sum('views'))['total'] or 0
	recent_likes = Video.objects.filter(created_at__gte=week_ago).aggregate(total=Sum('likes'))['total'] or 0
	recent_comments_count = Comment.objects.filter(created_at__gte=week_ago).count()
	
	# Get engagement trends (last 30 days)
	month_ago = timezone.now() - timedelta(days=30)
	engagement_trends = []
	for i in range(7):  # Last 7 days
		day_start = timezone.now() - timedelta(days=i+1)
		day_end = timezone.now() - timedelta(days=i)
		day_views = Video.objects.filter(created_at__gte=day_start, created_at__lt=day_end).aggregate(total=Sum('views'))['total'] or 0
		day_likes = Video.objects.filter(created_at__gte=day_start, created_at__lt=day_end).aggregate(total=Sum('likes'))['total'] or 0
		engagement_trends.append({
			'date': day_start.strftime('%Y-%m-%d'),
			'views': day_views,
			'likes': day_likes
		})
	
	context = {
		'total_videos': total_videos,
		'total_categories': total_categories,
		'total_tags': total_tags,
		'total_views': total_views,
		'total_likes': total_likes,
		'total_comments': total_comments,
		'avg_views_per_video': avg_views_per_video,
		'avg_likes_per_video': avg_likes_per_video,
		'recent_videos': recent_videos,
		'most_liked_videos': most_liked_videos,
		'most_viewed_videos': most_viewed_videos,
		'recent_comments': recent_comments,
		'videos_by_category': videos_by_category,
		'recent_uploads': recent_uploads,
		'recent_views': recent_views,
		'recent_likes': recent_likes,
		'recent_comments_count': recent_comments_count,
		'engagement_trends': engagement_trends,
	}
	return render(request, 'core/dashboard.html', context)


# Category CRUD
@login_required(login_url='login')
def category_list(request):
	categories = Category.objects.all()
	return render(request, 'core/category_list.html', {"categories": categories})


@login_required(login_url='login')
def category_create(request):
	if request.method == "POST":
		form = CategoryForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			messages.success(request, "Category created successfully")
			return redirect('category_list')
		else:
			messages.error(request, "Please correct the errors below.")
	else:
		form = CategoryForm()
	return render(request, 'core/category_form.html', {"form": form, "title": "Create Category"})


@login_required(login_url='login')
def category_update(request, pk: int):
	category = get_object_or_404(Category, pk=pk)
	if request.method == "POST":
		form = CategoryForm(request.POST, request.FILES, instance=category)
		if form.is_valid():
			form.save()
			messages.success(request, "Category updated successfully")
			return redirect('category_list')
		else:
			messages.error(request, "Please correct the errors below.")
	else:
		form = CategoryForm(instance=category)
	return render(request, 'core/category_form.html', {"form": form, "title": "Edit Category"})


@login_required(login_url='login')
def category_delete(request, pk: int):
	category = get_object_or_404(Category, pk=pk)
	if request.method == "POST":
		category.delete()
		messages.success(request, "Category deleted successfully")
		return redirect('category_list')
	return render(request, 'core/category_confirm_delete.html', {"object": category})


# Tag CRUD
@login_required(login_url='login')
def tag_list(request):
	tags = Tag.objects.all()
	return render(request, 'core/tag_list.html', {"tags": tags})


@login_required(login_url='login')
def tag_create(request):
	if request.method == "POST":
		form = TagForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, "Tag created successfully")
			return redirect('tag_list')
	else:
		form = TagForm()
	return render(request, 'core/tag_form.html', {"form": form, "title": "Create Tag"})


@login_required(login_url='login')
def tag_update(request, pk: int):
	tag = get_object_or_404(Tag, pk=pk)
	if request.method == "POST":
		form = TagForm(request.POST, instance=tag)
		if form.is_valid():
			form.save()
			messages.success(request, "Tag updated successfully")
			return redirect('tag_list')
	else:
		form = TagForm(instance=tag)
	return render(request, 'core/tag_form.html', {"form": form, "title": "Edit Tag"})


@login_required(login_url='login')
def tag_delete(request, pk: int):
	tag = get_object_or_404(Tag, pk=pk)
	if request.method == "POST":
		tag.delete()
		messages.success(request, "Tag deleted successfully")
		return redirect('tag_list')
	return render(request, 'core/tag_confirm_delete.html', {"object": tag})


# Video CRUD
@login_required(login_url='login')
def video_list(request):
	videos = Video.objects.select_related('uploader').prefetch_related('category', 'tags').all()
	return render(request, 'core/video_list.html', {"videos": videos})


@login_required(login_url='login')
def video_create(request):
	if request.method == "POST":
		form = VideoForm(request.POST, request.FILES)
		if form.is_valid():
			try:
				video = form.save(commit=False)
				if request.user.is_authenticated:
					video.uploader = request.user
				video.save()
				form.save_m2m()
				
				# Generate thumbnail if no thumbnail provided and video file exists
				# if not video.thumbnail and video.video_file:
				# 	video.generate_thumbnail()
				# 	video.save()  # Save again to store the generated thumbnail
				
				messages.success(request, "Video created successfully")
				return redirect('video_list')
			except Exception as e:
				messages.error(request, f"Error creating video: {str(e)}")
				print(f"Video creation error: {e}")  # Debug print
		else:
			# Form is not valid, show errors
			error_messages = []
			for field, errors in form.errors.items():
				for error in errors:
					error_messages.append(f"{field}: {error}")
			messages.error(request, f"Form validation errors: {'; '.join(error_messages)}")
			print(f"Form errors: {form.errors}")  # Debug print
	else:
		form = VideoForm()
	return render(request, 'core/video_form.html', {"form": form, "title": "Create Video"})


@login_required(login_url='login')
def video_update(request, pk: int):
	video = get_object_or_404(Video, pk=pk)
	if request.method == "POST":
		form = VideoForm(request.POST, request.FILES, instance=video)
		if form.is_valid():
			form.save()
			
			# Generate thumbnail if no thumbnail provided and video file exists
			if not video.thumbnail and video.video_file:
				video.generate_thumbnail()
				video.save()  # Save again to store the generated thumbnail
			
			messages.success(request, "Video updated successfully")
			return redirect('video_list')
	else:
		form = VideoForm(instance=video)
	return render(request, 'core/video_form.html', {"form": form, "title": "Edit Video"})


@login_required(login_url='login')
def video_delete(request, pk: int):
	video = get_object_or_404(Video, pk=pk)
	if request.method == "POST":
		video.delete()
		messages.success(request, "Video deleted successfully")
		return redirect('video_list')
	return render(request, 'core/video_confirm_delete.html', {"object": video})


@login_required(login_url='login')
@require_http_methods(["POST"])
def video_toggle_status(request, pk: int):
	"""Toggle video active status via AJAX"""
	try:
		video = get_object_or_404(Video, pk=pk)
		
		# Parse JSON data
		data = json.loads(request.body)
		is_active = data.get('is_active', False)
		
		# Update video status
		video.is_active = is_active
		video.save(update_fields=['is_active'])
		
		return JsonResponse({
			'success': True,
			'message': f'Video {"activated" if is_active else "deactivated"} successfully',
			'is_active': video.is_active
		})
		
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		}, status=400)


# CMS Views
@login_required(login_url='login')
def cms_list(request):
	"""List all CMS pages"""
	cms_pages = CMS.objects.all()
	context = {
		'cms_pages': cms_pages,
	}
	return render(request, 'core/cms_list.html', context)


@login_required(login_url='login')
def cms_create(request):
	"""Create a new CMS page"""
	if request.method == 'POST':
		form = CMSForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'CMS page created successfully.')
			return redirect('cms_list')
	else:
		form = CMSForm()
	
	context = {
		'form': form,
	}
	return render(request, 'core/cms_form.html', context)


@login_required(login_url='login')
def cms_update(request, pk):
	"""Update a CMS page"""
	cms_page = get_object_or_404(CMS, pk=pk)
	
	if request.method == 'POST':
		form = CMSForm(request.POST, instance=cms_page)
		if form.is_valid():
			form.save()
			messages.success(request, 'CMS page updated successfully.')
			return redirect('cms_list')
	else:
		form = CMSForm(instance=cms_page)
	
	context = {
		'form': form,
		'cms_page': cms_page,
	}
	return render(request, 'core/cms_form.html', context)


@login_required(login_url='login')
def cms_delete(request, pk):
	"""Delete a CMS page"""
	cms_page = get_object_or_404(CMS, pk=pk)
	
	if request.method == 'POST':
		cms_page.delete()
		messages.success(request, 'CMS page deleted successfully.')
		return redirect('cms_list')
	
	context = {
		'cms_page': cms_page,
	}
	return render(request, 'core/cms_confirm_delete.html', context)


@login_required(login_url='login')
def cms_detail(request, slug):
	"""View a CMS page"""
	cms_page = get_object_or_404(CMS, slug=slug, is_active=True)
	context = {
		'cms_page': cms_page,
	}
	return render(request, 'core/cms_detail.html', context)


# Settings Views
@login_required(login_url='login')
def settings_list(request):
	"""List all settings"""
	settings = Settings.objects.all()
	context = {
		'settings': settings,
	}
	return render(request, 'core/settings_list.html', context)


@login_required(login_url='login')
def settings_create(request):
	"""Create a new setting"""
	if request.method == 'POST':
		form = SettingsForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Setting created successfully.')
			return redirect('settings_list')
	else:
		form = SettingsForm()
	
	context = {
		'form': form,
	}
	return render(request, 'core/settings_form.html', context)


@login_required(login_url='login')
def settings_update(request, pk):
	"""Update a setting"""
	setting = get_object_or_404(Settings, pk=pk)
	
	if request.method == 'POST':
		form = SettingsForm(request.POST, instance=setting)
		if form.is_valid():
			form.save()
			messages.success(request, 'Setting updated successfully.')
			return redirect('settings_list')
	else:
		form = SettingsForm(instance=setting)
	
	context = {
		'form': form,
		'setting': setting,
	}
	return render(request, 'core/settings_form.html', context)


@login_required(login_url='login')
def settings_delete(request, pk):
	"""Delete a setting"""
	setting = get_object_or_404(Settings, pk=pk)
	
	if request.method == 'POST':
		setting.delete()
		messages.success(request, 'Setting deleted successfully.')
		return redirect('settings_list')
	
	context = {
		'setting': setting,
	}
	return render(request, 'core/settings_confirm_delete.html', context)


# Age Verification Views
@login_required(login_url='login')
def age_verification_list(request):
	"""List all age verification modals"""
	age_verifications = AgeVerification.objects.all()
	context = {
		'age_verifications': age_verifications,
	}
	return render(request, 'core/age_verification_list.html', context)


@login_required(login_url='login')
def age_verification_create(request):
	"""Create a new age verification modal"""
	if request.method == 'POST':
		form = AgeVerificationForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Age verification modal created successfully.')
			return redirect('age_verification_list')
	else:
		form = AgeVerificationForm()
	
	context = {
		'form': form,
	}
	return render(request, 'core/age_verification_form.html', context)


@login_required(login_url='login')	
def age_verification_update(request, pk):
	"""Update an age verification modal"""
	age_verification = get_object_or_404(AgeVerification, pk=pk)
	
	if request.method == 'POST':
		form = AgeVerificationForm(request.POST, instance=age_verification)
		if form.is_valid():
			form.save()
			messages.success(request, 'Age verification modal updated successfully.')
			return redirect('age_verification_list')
	else:
		form = AgeVerificationForm(instance=age_verification)
	
	context = {
		'form': form,
		'age_verification': age_verification,
	}
	return render(request, 'core/age_verification_form.html', context)


@login_required(login_url='login')
def age_verification_delete(request, pk):
	"""Delete an age verification modal"""
	age_verification = get_object_or_404(AgeVerification, pk=pk)
	
	if request.method == 'POST':
		age_verification.delete()
		messages.success(request, 'Age verification modal deleted successfully.')
		return redirect('age_verification_list')
	
	context = {
		'age_verification': age_verification,
	}
	return render(request, 'core/age_verification_confirm_delete.html', context)


@login_required(login_url='login')
def age_verification_detail(request, pk):
	"""View an age verification modal"""
	age_verification = get_object_or_404(AgeVerification, pk=pk)
	context = {
		'age_verification': age_verification,
	}
	return render(request, 'core/age_verification_detail.html', context)


# User Management Views
@login_required(login_url='login')
def user_list(request):
	"""List all users"""
	users = User.objects.all().order_by('-date_joined')
	context = {
		'users': users,
	}
	return render(request, 'core/user_list.html', context)


@login_required(login_url='login')
def user_detail(request, pk):
	"""View user details"""
	user = get_object_or_404(User, pk=pk)
	context = {
		'user': user,
	}
	return render(request, 'core/user_detail.html', context)


@login_required(login_url='login')
def user_update(request, pk):
	"""Update user"""
	user = get_object_or_404(User, pk=pk)
	
	if request.method == 'POST':
		name = request.POST.get('name')
		email = request.POST.get('email')
		is_staff = request.POST.get('is_staff') == 'on'
		is_active = request.POST.get('is_active') == 'on'
		is_freeze = request.POST.get('is_freeze') == 'on'
		
		user.name = name
		user.email = email
		user.is_staff = is_staff
		user.is_active = is_active
		user.is_freeze = is_freeze
		user.save()
		
		messages.success(request, 'User updated successfully.')
		return redirect('user_detail', pk=user.pk)
	
	context = {
		'user': user,
	}
	return render(request, 'core/user_form.html', context)


@login_required(login_url='login')	
def user_delete(request, pk):
	"""Delete user"""
	user = get_object_or_404(User, pk=pk)
	
	if request.method == 'POST':
		user.delete()
		messages.success(request, 'User deleted successfully.')
		return redirect('user_list')
	
	context = {
		'user': user,
	}
	return render(request, 'core/user_confirm_delete.html', context)