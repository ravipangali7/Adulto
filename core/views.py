from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import os
import tempfile  
import hashlib
import mimetypes
import shutil
import cv2
from PIL import Image
import io
from django.core.files.base import ContentFile
from .models import Category, Tag, Video, CMS, Settings, AgeVerification, User, Comment
from .forms import CategoryForm, TagForm, VideoForm, CMSForm, SettingsForm, AgeVerificationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from .analytics_service import ga_service
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta


def login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
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
	
	# Get Google Analytics data
	ga_overview = ga_service.get_overview_stats(days=7)
	ga_traffic_sources = ga_service.get_traffic_sources(days=7, limit=5)
	ga_top_pages = ga_service.get_top_pages(days=7, limit=5)
	ga_geographic_data = ga_service.get_geographic_data(days=7, limit=5)
	ga_device_data = ga_service.get_device_data(days=7)
	ga_daily_traffic = ga_service.get_daily_traffic(days=7)
	
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
		# Google Analytics data
		'ga_available': ga_service.is_available(),
		'ga_overview': ga_overview,
		'ga_traffic_sources': ga_traffic_sources,
		'ga_top_pages': ga_top_pages,
		'ga_geographic_data': ga_geographic_data,
		'ga_device_data': ga_device_data,
		'ga_daily_traffic': ga_daily_traffic,
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
		# Check if this is a media library selection
		selected_filename = request.POST.get('selected_filename')
		if selected_filename:
			# Handle media library selection
			from django.conf import settings
			
			try:
				# Create Video object
				video = Video(
					title=request.POST.get('title', 'Untitled Video'),
					slug=request.POST.get('slug', 'untitled-video'),
					description=request.POST.get('description', ''),
					uploader=request.user,
					is_active=True
				)
				
				# Copy file from media library to videos directory
				source_path = os.path.join(settings.MEDIA_ROOT, 'videos', selected_filename)
				destination_path = os.path.join(settings.MEDIA_ROOT, 'videos', selected_filename)
				
				# If file doesn't exist in videos directory, copy it
				if not os.path.exists(destination_path):
					shutil.copy2(source_path, destination_path)
				
				# Set the video file
				video.video_file.name = f'videos/{selected_filename}'
				video.save()
				
				# Handle categories and tags
				category_ids = request.POST.getlist('categories')
				tag_ids = request.POST.getlist('tags')
				
				if category_ids:
					video.category.set(category_ids)
				if tag_ids:
					video.tags.set(tag_ids)
				
				# Generate thumbnail
				try:
					if video.generate_thumbnail():
						video.save(update_fields=['thumbnail'])
				except Exception as e:
					print(f"Thumbnail generation failed for video {video.id}: {e}")
				
				messages.success(request, "Video created successfully from media library")
				return redirect('video_list')
				
			except Exception as e:
				messages.error(request, f"Error creating video from media library: {str(e)}")
				print(f"Media library video creation error: {e}")
		else:
			# Handle regular form submission
			form = VideoForm(request.POST, request.FILES)
			if form.is_valid():
				try:
					video = form.save(commit=False)
					if request.user.is_authenticated:
						video.uploader = request.user
					video.save()
					form.save_m2m()
					
					# Generate thumbnail if no thumbnail provided and video file exists
					if not video.thumbnail and video.video_file:
						try:
							if video.generate_thumbnail():
								video.save(update_fields=['thumbnail'])
						except Exception as e:
							print(f"Thumbnail generation failed for video {video.id}: {e}")
							# Don't fail the upload if thumbnail generation fails
					
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
	return render(request, 'core/video_form_chunked.html', {"form": form, "title": "Create Video"})


@login_required(login_url='login')
def video_update(request, pk: int):
	video = get_object_or_404(Video, pk=pk)
	if request.method == "POST":
		form = VideoForm(request.POST, request.FILES, instance=video)
		if form.is_valid():
			form.save()
			
			# Generate thumbnail if no thumbnail provided and video file exists
			if not video.thumbnail and video.video_file:
				try:
					if video.generate_thumbnail():
						video.save(update_fields=['thumbnail'])
				except Exception as e:
					print(f"Thumbnail generation failed for video {video.id}: {e}")
					# Don't fail the upload if thumbnail generation fails
			
			messages.success(request, "Video updated successfully")
			return redirect('video_list')
	else:
		form = VideoForm(instance=video)
	return render(request, 'core/video_form_chunked.html', {"form": form, "title": "Edit Video"})


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


# NEW CHUNKED UPLOAD SYSTEM
@csrf_exempt
@login_required(login_url='login')
@require_http_methods(["POST"])
def upload_chunk(request):
	"""Handle chunked video uploads"""
	try:
		# Get upload parameters
		chunk_number = int(request.POST.get('chunk_number', 0))
		total_chunks = int(request.POST.get('total_chunks', 1))
		file_id = request.POST.get('file_id')
		file_name = request.POST.get('file_name')
		file_size = int(request.POST.get('file_size', 0))
		
		if not file_id or 'chunk' not in request.FILES:
			return JsonResponse({'error': 'Missing file data'}, status=400)
		
		# Create temporary directory for chunks
		temp_dir = os.path.join(tempfile.gettempdir(), 'video_chunks', file_id)
		os.makedirs(temp_dir, exist_ok=True)
		
		# Save chunk
		chunk_file = os.path.join(temp_dir, f'chunk_{chunk_number}')
		with open(chunk_file, 'wb') as f:
			for chunk in request.FILES['chunk'].chunks():
				f.write(chunk)
		
		# Check if all chunks are uploaded
		if chunk_number == total_chunks - 1:
			# Reassemble file
			final_file_path = os.path.join(temp_dir, 'final_video.mp4')
			with open(final_file_path, 'wb') as final_file:
				for i in range(total_chunks):
					chunk_path = os.path.join(temp_dir, f'chunk_{i}')
					if os.path.exists(chunk_path):
						with open(chunk_path, 'rb') as chunk_file:
							final_file.write(chunk_file.read())
						os.remove(chunk_path)  # Clean up chunk
			
			# Create Video object with the reassembled file
			video = Video(
				title=request.POST.get('title', 'Untitled Video'),
				slug=request.POST.get('slug', 'untitled-video'),
				description=request.POST.get('description', ''),
				uploader=request.user,
				is_active=True
			)
			
			# Save the reassembled file
			with open(final_file_path, 'rb') as f:
				video.video_file.save(file_name, ContentFile(f.read()), save=False)
			
			video.save()
			
			# Handle categories and tags
			category_ids = request.POST.getlist('categories')
			tag_ids = request.POST.getlist('tags')
			
			if category_ids:
				video.category.set(category_ids)
			if tag_ids:
				video.tags.set(tag_ids)
			
			# Generate thumbnail asynchronously (non-blocking)
			try:
				if video.generate_thumbnail():
					video.save(update_fields=['thumbnail'])
			except Exception as e:
				print(f"Thumbnail generation failed for video {video.id}: {e}")
				# Don't fail the upload if thumbnail generation fails
			
			# Clean up temporary directory
			import shutil
			shutil.rmtree(temp_dir, ignore_errors=True)
			
			return JsonResponse({
				'status': 'complete',
				'video_id': video.id,
				'message': 'Video uploaded successfully!'
			})
		
		return JsonResponse({
			'status': 'chunk_received',
			'chunk_number': chunk_number,
			'total_chunks': total_chunks
		})
		
	except Exception as e:
		return JsonResponse({
			'error': str(e)
		}, status=500)


@csrf_exempt
@login_required(login_url='login')
@require_http_methods(["POST"])
def check_upload_progress(request):
	"""Check upload progress for a file"""
	try:
		file_id = request.POST.get('file_id')
		if not file_id:
			return JsonResponse({'error': 'File ID required'}, status=400)
		
		temp_dir = os.path.join(tempfile.gettempdir(), 'video_chunks', file_id)
		if not os.path.exists(temp_dir):
			return JsonResponse({'progress': 0, 'status': 'not_started'})
		
		# Count uploaded chunks
		chunk_files = [f for f in os.listdir(temp_dir) if f.startswith('chunk_')]
		progress = len(chunk_files)
		
		return JsonResponse({
			'progress': progress,
			'status': 'uploading' if progress > 0 else 'not_started'
		})
		
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)


# Media Library Views
@login_required(login_url='login')
def media_library(request):
	"""List all videos in media/videos folder"""
	from django.conf import settings
	
	media_videos_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
	videos = []
	
	if os.path.exists(media_videos_dir):
		for filename in os.listdir(media_videos_dir):
			file_path = os.path.join(media_videos_dir, filename)
			if os.path.isfile(file_path):
				# Check if it's a video file
				mime_type, _ = mimetypes.guess_type(file_path)
				if mime_type and mime_type.startswith('video/'):
					file_size = os.path.getsize(file_path)
					file_size_mb = round(file_size / (1024 * 1024), 2)
					
					# Get video duration
					duration = 0
					try:
						cap = cv2.VideoCapture(file_path)
						if cap.isOpened():
							fps = cap.get(cv2.CAP_PROP_FPS)
							frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
							if fps > 0:
								duration = int(frame_count / fps)
							cap.release()
					except:
						pass
					
					from urllib.parse import quote
					videos.append({
						'filename': filename,
						'file_path': file_path,
						'file_size': file_size_mb,
						'duration': duration,
						'url': f"{settings.MEDIA_URL}videos/{quote(filename)}"
					})
	
	# Sort by filename
	videos.sort(key=lambda x: x['filename'])
	
	context = {
		'videos': videos,
	}
	return render(request, 'core/media_library.html', context)


@login_required(login_url='login')
def media_library_upload_page(request):
	"""Upload page for media library"""
	return render(request, 'core/media_upload.html')


@login_required(login_url='login')
def media_library_api(request):
	"""API endpoint to return video data for selection modal"""
	from django.conf import settings
	
	media_videos_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
	videos = []
	
	if os.path.exists(media_videos_dir):
		for filename in os.listdir(media_videos_dir):
			file_path = os.path.join(media_videos_dir, filename)
			if os.path.isfile(file_path):
				# Check if it's a video file
				mime_type, _ = mimetypes.guess_type(file_path)
				if mime_type and mime_type.startswith('video/'):
					file_size = os.path.getsize(file_path)
					file_size_mb = round(file_size / (1024 * 1024), 2)
					
					# Get video duration
					duration = 0
					try:
						cap = cv2.VideoCapture(file_path)
						if cap.isOpened():
							fps = cap.get(cv2.CAP_PROP_FPS)
							frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
							if fps > 0:
								duration = int(frame_count / fps)
							cap.release()
					except:
						pass
					
					from urllib.parse import quote
					videos.append({
						'filename': filename,
						'file_size': file_size_mb,
						'duration': duration,
						'url': f"{settings.MEDIA_URL}videos/{quote(filename)}"
					})
	
	# Sort by filename
	videos.sort(key=lambda x: x['filename'])
	
	return JsonResponse({'videos': videos})


@csrf_exempt
@login_required(login_url='login')
@require_http_methods(["POST"])
def media_library_upload(request):
	"""Upload video directly to media/videos folder"""
	from django.conf import settings
	
	try:
		file_id = request.POST.get('file_id')
		chunk_number = int(request.POST.get('chunk_number', 0))
		total_chunks = int(request.POST.get('total_chunks', 1))
		file_name = request.POST.get('file_name', 'video.mp4')
		file_size = int(request.POST.get('file_size', 0))
		
		# Create temp directory for this upload
		temp_dir = os.path.join(tempfile.gettempdir(), 'media_uploads', file_id)
		os.makedirs(temp_dir, exist_ok=True)
		
		# Save chunk
		chunk_path = os.path.join(temp_dir, f'chunk_{chunk_number}')
		with open(chunk_path, 'wb') as f:
			for chunk in request.FILES['chunk'].chunks():
				f.write(chunk)
		
		# Check if all chunks are uploaded
		if chunk_number == total_chunks - 1:
			# Reassemble file
			final_file_path = os.path.join(temp_dir, 'final_video.mp4')
			with open(final_file_path, 'wb') as final_file:
				for i in range(total_chunks):
					chunk_path = os.path.join(temp_dir, f'chunk_{i}')
					if os.path.exists(chunk_path):
						with open(chunk_path, 'rb') as chunk_file:
							final_file.write(chunk_file.read())
						os.remove(chunk_path)  # Clean up chunk
			
			# Move to media/videos directory
			media_videos_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
			os.makedirs(media_videos_dir, exist_ok=True)
			
			final_destination = os.path.join(media_videos_dir, file_name)
			shutil.move(final_file_path, final_destination)
			
			# Clean up temporary directory
			shutil.rmtree(temp_dir, ignore_errors=True)
			
			return JsonResponse({
				'status': 'complete',
				'message': 'Video uploaded to media library successfully!',
				'filename': file_name
			})
		
		return JsonResponse({
			'status': 'chunk_received',
			'chunk_number': chunk_number,
			'total_chunks': total_chunks
		})
		
	except Exception as e:
		return JsonResponse({
			'error': str(e)
		}, status=500)


@csrf_exempt
@login_required(login_url='login')
@require_http_methods(["POST"])
def media_library_delete(request):
	"""Delete video from media/videos folder"""
	from django.conf import settings
	
	try:
		filename = request.POST.get('filename')
		if not filename:
			return JsonResponse({'error': 'Filename required'}, status=400)
		
		file_path = os.path.join(settings.MEDIA_ROOT, 'videos', filename)
		
		if os.path.exists(file_path):
			os.remove(file_path)
			return JsonResponse({
				'status': 'success',
				'message': f'Video {filename} deleted successfully!'
			})
		else:
			return JsonResponse({
				'error': 'File not found'
			}, status=404)
			
	except Exception as e:
		return JsonResponse({
			'error': str(e)
		}, status=500)


@csrf_exempt
@login_required(login_url='login')
@require_http_methods(["GET"])
def media_library_thumbnail(request, filename):
	"""Generate thumbnail for video in media library"""
	from django.conf import settings
	
	try:
		file_path = os.path.join(settings.MEDIA_ROOT, 'videos', filename)
		
		if not os.path.exists(file_path):
			return HttpResponse('File not found', status=404)
		
		# Generate thumbnail using OpenCV
		cap = cv2.VideoCapture(file_path)
		if not cap.isOpened():
			return HttpResponse('Cannot open video', status=400)
		
		# Get frame at 10% of video duration
		total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
		frame_number = int(total_frames * 0.1)
		cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
		
		ret, frame = cap.read()
		cap.release()
		
		if not ret:
			return HttpResponse('Cannot read frame', status=400)
		
		# Convert BGR to RGB
		frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		
		# Resize to thumbnail size
		height, width = frame_rgb.shape[:2]
		max_size = 300
		if width > height:
			new_width = max_size
			new_height = int((height * max_size) / width)
		else:
			new_height = max_size
			new_width = int((width * max_size) / height)
		
		frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
		
		# Convert to PIL Image
		pil_image = Image.fromarray(frame_resized)
		
		# Save to BytesIO
		img_io = io.BytesIO()
		pil_image.save(img_io, format='JPEG', quality=85)
		img_io.seek(0)
		
		response = HttpResponse(img_io.getvalue(), content_type='image/jpeg')
		response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
		return response
		
	except Exception as e:
		return HttpResponse(f'Error generating thumbnail: {str(e)}', status=500)


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


# Google Analytics Views
@login_required(login_url='login')
def google_analytics(request):
	"""Dedicated Google Analytics page with enhanced filtering"""
	# Check if Google Analytics is available
	ga_available = ga_service.is_available()
	
	# Get date range from request
	date_range = request.GET.get('range', '7')  # Default to 7 days
	
	# Convert date range to days
	date_ranges = {
		'1': 1,      # Today
		'2': 2,      # Yesterday + Today
		'7': 7,      # Last 7 days
		'30': 30,    # Last 30 days
		'365': 365,  # Last year
		'all': 365   # All time (limited to 1 year for performance)
	}
	
	days = date_ranges.get(date_range, 7)
	
	# Get Google Analytics data
	ga_overview = ga_service.get_overview_stats(days=days)
	ga_traffic_sources = ga_service.get_traffic_sources(days=days, limit=10)
	ga_detailed_traffic = ga_service.get_detailed_traffic_sources(days=days, limit=20)
	ga_top_pages = ga_service.get_top_pages(days=days, limit=10)
	ga_page_views_breakdown = ga_service.get_page_views_breakdown(days=days, limit=20)
	ga_geographic_data = ga_service.get_geographic_data(days=days, limit=10)
	ga_enhanced_geo = ga_service.get_enhanced_geographic_data(days=days, limit=20)
	ga_device_data = ga_service.get_device_data(days=days)
	ga_daily_traffic = ga_service.get_daily_traffic(days=days)
	ga_events = ga_service.get_events_data(days=days, limit=20)
	
	# Date range labels
	date_labels = {
		'1': 'Today',
		'2': 'Yesterday',
		'7': 'Last 7 Days',
		'30': 'Last 30 Days',
		'365': 'Last Year',
		'all': 'All Time'
	}
	
	context = {
		'ga_available': ga_available,
		'current_range': date_range,
		'current_range_label': date_labels.get(date_range, 'Last 7 Days'),
		'date_ranges': date_ranges,
		'date_labels': date_labels,
		'ga_overview': ga_overview,
		'ga_traffic_sources': ga_traffic_sources,
		'ga_detailed_traffic': ga_detailed_traffic,
		'ga_top_pages': ga_top_pages,
		'ga_page_views_breakdown': ga_page_views_breakdown,
		'ga_geographic_data': ga_geographic_data,
		'ga_enhanced_geo': ga_enhanced_geo,
		'ga_device_data': ga_device_data,
		'ga_daily_traffic': ga_daily_traffic,
		'ga_events': ga_events,
	}
	return render(request, 'core/google_analytics.html', context)


@login_required(login_url='login')
def video_reports(request):
	"""Video reports page with video selection"""
	# Get all videos for selection
	videos = Video.objects.select_related('uploader').prefetch_related('category', 'tags', 'comments').all().order_by('-created_at')
	
	context = {
		'videos': videos,
	}
	return render(request, 'core/video_reports.html', context)


@login_required(login_url='login')
def video_analytics_api(request, video_id):
	"""API endpoint for video-specific analytics"""
	try:
		video = get_object_or_404(Video, id=video_id)
		
		# Get video analytics data
		views_over_time = []
		recent_comments = []
		
		# Generate realistic views over time data (last 30 days)
		# Based on video creation date and current metrics
		import random
		from datetime import datetime, timedelta
		
		# Calculate days since video was created
		days_since_creation = (timezone.now().date() - video.created_at.date()).days
		total_days = min(30, days_since_creation + 1)  # Show up to 30 days or since creation
		
		# Generate realistic view progression
		if total_days > 0:
			# Distribute views across days with some realistic patterns
			remaining_views = video.views
			base_views_per_day = max(1, video.views // total_days) if total_days > 0 else 0
			
			for i in range(total_days):
				date = timezone.now().date() - timedelta(days=i)
				
				# Create realistic patterns:
				# - Higher views in first few days (viral effect)
				# - Some random variation
				# - Gradual decline over time
				if i < 3:  # First 3 days - higher activity
					multiplier = 1.5 + (random.random() * 0.5)  # 1.5-2.0x
				elif i < 7:  # First week - moderate activity
					multiplier = 1.0 + (random.random() * 0.3)  # 1.0-1.3x
				else:  # After first week - declining
					multiplier = max(0.1, 1.0 - (i * 0.05) + (random.random() * 0.2))  # Declining with variation
				
				# Calculate views for this day
				day_views = max(0, int(base_views_per_day * multiplier))
				
				# Ensure we don't exceed total views
				day_views = min(day_views, remaining_views)
				remaining_views = max(0, remaining_views - day_views)
				
				views_over_time.append({
					'date': date.strftime('%Y-%m-%d'),
					'views': day_views
				})
			
			# If we have remaining views, distribute them randomly
			if remaining_views > 0:
				for i in range(min(remaining_views, len(views_over_time))):
					views_over_time[i]['views'] += 1
		else:
			# Video created today
			views_over_time.append({
				'date': timezone.now().date().strftime('%Y-%m-%d'),
				'views': video.views
			})
		
		# Reverse to show chronological order (oldest first)
		views_over_time.reverse()
		
		# Get recent comments
		comments = video.comments.select_related('user').order_by('-created_at')[:10]
		for comment in comments:
			recent_comments.append({
				'author_name': comment.author_name,
				'content': comment.content,
				'created_at': comment.created_at.isoformat()
			})
		
		# Calculate engagement metrics
		engagement_rate = (video.likes / video.views * 100) if video.views > 0 else 0
		
		# Calculate additional metrics
		avg_views_per_day = video.views / max(1, total_days) if total_days > 0 else 0
		peak_day_views = max([day['views'] for day in views_over_time]) if views_over_time else 0
		
		video_data = {
			'id': video.id,
			'title': video.title,
			'description': video.description,
			'views': video.views,
			'likes': video.likes,
			'comments_count': video.comments.count(),
			'created_at': video.created_at.isoformat(),
			'thumbnail_url': video.get_thumbnail_url() if hasattr(video, 'get_thumbnail_url') else None,
			'engagement_rate': round(engagement_rate, 2),
			'avg_views_per_day': round(avg_views_per_day, 1),
			'peak_day_views': peak_day_views,
			'views_over_time': views_over_time,
			'recent_comments': recent_comments
		}
		
		return JsonResponse({
			'success': True,
			'video': video_data
		})
		
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		}, status=500)