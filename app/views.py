from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, FileResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.http import http_date
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import authenticate
import os
import mimetypes
import json
from core.models import Video, Category, Tag, Comment, CMS
from django.contrib.auth.decorators import login_required
from core.forms import CommentForm

def home(request):
    """Home page view with categories and videos"""
    categories = Category.objects.all()
    videos = Video.objects.filter(is_active=True) 
    tags = Tag.objects.all()
    context = {
        'categories': categories,
        'videos': videos,
        'tags': tags,
    }
    return render(request, 'site/home.html', context)

def videos(request):
    """All videos page with filtering"""
    categories = Category.objects.all()
    tags = Tag.objects.all()
    videos = Video.objects.filter(is_active=True)
    
    # Filter by category if provided
    category_slug = request.GET.get('category')
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            videos = videos.filter(category=category)
        except Category.DoesNotExist:
            pass
    
    # Filter by tag if provided
    tag_slug = request.GET.get('tag')
    if tag_slug:
        try:
            tag = Tag.objects.get(slug=tag_slug)
            videos = videos.filter(tags=tag)
        except Tag.DoesNotExist:
            pass
    
    # Sort videos by creation date (newest first)
    videos = videos.order_by('-created_at')
    
    context = {
        'categories': categories,
        'tags': tags,
        'videos': videos,
        'current_category': category_slug,
        'current_tag': tag_slug,
    }
    return render(request, 'site/videos.html', context)

def video_detail(request, slug):
    """Video detail page"""
    video = get_object_or_404(Video, slug=slug, is_active=True)
    # Increment view count
    video.views += 1
    video.save(update_fields=['views'])
    
    # Get related videos (same categories, only active)
    related_videos = Video.objects.filter(
        category__in=video.category.all(),
        is_active=True
    ).exclude(id=video.id).distinct()
    
    # Get popular videos for sidebar (top 6 by views)
    popular_videos = Video.objects.filter(
        is_active=True
    ).exclude(id=video.id).order_by('-views')[:6]
    
    # Get approved comments
    comments = Comment.objects.filter(video=video, is_approved=True).select_related('user')
    
    # Initialize comment form
    comment_form = CommentForm(user=request.user)
    
    context = {
        'video': video,
        'related_videos': related_videos,
        'popular_videos': popular_videos,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'site/video_detail.html', context)

def categories(request):
    """Categories page"""
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'site/categories.html', context)

def tags(request):
    """Tags page"""
    tags = Tag.objects.all()
    context = {
        'tags': tags,
    }
    return render(request, 'site/tags.html', context)

def latest(request):
    """Latest videos page"""
    videos = Video.objects.filter(is_active=True).order_by('-created_at')
    context = {
        'videos': videos,
    }
    return render(request, 'site/latest.html', context)

def popular(request):
    """Popular videos page"""
    videos = Video.objects.filter(is_active=True).order_by('-views')
    context = {
        'videos': videos,
    }
    return render(request, 'site/popular.html', context)

def login_view(request):
    """Login page with activation check"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_email_verified:
                from django.contrib.auth import login as auth_login
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Please check your email and activate your account before logging in.')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'site/login.html')

def signup_view(request):
    """Signup page with email activation"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation
        if not name or not name.strip():
            messages.error(request, 'Please enter your full name.')
        elif not email or not email.strip():
            messages.error(request, 'Please enter a valid email address.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            try:
                from core.models import User
                from core.utils import send_verification_email
                
                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'An account with this email already exists. Please try logging in instead.')
                    return render(request, 'site/signup.html')
                
                # Create user but don't activate
                user = User(
                    email=email,
                    name=name.strip(),
                    is_staff=False,  # Will be True after email verification
                    is_email_verified=False
                )
                user.set_password(password)
                user.save()
                
                # Send verification email
                try:
                    if send_verification_email(user, request):
                        messages.success(request, f'Account created successfully! Please check your email ({email}) and click the activation link to complete your registration. If you don\'t see the email, check your spam folder.')
                        return redirect('login')
                    else:
                        messages.error(request, 'Account created but failed to send verification email. Please try again or contact support.')
                except Exception as email_error:
                    print(f"Email sending error: {email_error}")
                    messages.error(request, f'Account created but email sending failed: {str(email_error)}. Please contact support.')
                    
            except Exception as e:
                print(f"User creation error: {e}")
                if 'email' in str(e).lower():
                    messages.error(request, 'An account with this email already exists.')
                else:
                    messages.error(request, f'An error occurred while creating your account: {str(e)}')
    
    return render(request, 'site/signup.html')

def logout_view(request):
    """Logout user"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')

@require_http_methods(["GET", "HEAD"])
def stream_video(request, video_id):
    """
    Stream video with HTTP Range Request support for seeking
    """
    try:
        video = Video.objects.get(id=video_id, is_active=True)
        video_path = video.video_file.path
    except Video.DoesNotExist:
        raise Http404("Video not found")
    
    if not os.path.exists(video_path):
        raise Http404("Video file not found")
    
    file_size = os.path.getsize(video_path)
    range_header = request.META.get('HTTP_RANGE', '').strip()
    
    # Get content type
    content_type, _ = mimetypes.guess_type(video_path)
    if not content_type:
        content_type = 'video/mp4'
    
    if range_header:
        # Parse range header
        range_match = range_header.replace('bytes=', '').split('-')
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        
        # Ensure end doesn't exceed file size
        end = min(end, file_size - 1)
        
        # Calculate content length
        content_length = end - start + 1
        
        # Create response with partial content
        response = HttpResponse(status=206)
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Content-Length'] = str(content_length)
        response['Content-Type'] = content_type
        
        # Open file and seek to start position
        with open(video_path, 'rb') as f:
            f.seek(start)
            response.write(f.read(content_length))
        
        return response
    else:
        # No range request - serve entire file
        response = FileResponse(
            open(video_path, 'rb'),
            content_type=content_type
        )
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        response['Last-Modified'] = http_date(os.path.getmtime(video_path))
        return response


def search(request):
    """Comprehensive search functionality"""
    query = request.GET.get('q', '').strip()
    results = []
    total_results = 0
    search_categories = []
    search_tags = []
    
    if query:
        # Search in videos (title, description, uploader name)
        video_results = Video.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(uploader__name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().order_by('-created_at')
        
        # Search in categories
        search_categories = Category.objects.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query)
        ).distinct()
        
        # Search in tags
        search_tags = Tag.objects.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query)
        ).distinct()
        
        # Combine all video results
        results = video_results
        total_results = results.count()
        
        # Pagination
        paginator = Paginator(results, 12)  # 12 videos per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = None
    
    # Get all categories and tags for sidebar
    all_categories = Category.objects.all()
    all_tags = Tag.objects.all()
    
    context = {
        'query': query,
        'results': page_obj,
        'total_results': total_results,
        'search_categories': search_categories,
        'search_tags': search_tags,
        'all_categories': all_categories,
        'all_tags': all_tags,
        'has_results': total_results > 0 if query else False,
    }
    
    return render(request, 'site/search.html', context)


def not_found(request, exception=None, path=None):
    """Custom 404 page"""
    context = {
        'error_code': '404',
        'error_title': 'Page Not Found',
        'error_message': 'The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.',
    }
    return render(request, 'site/error.html', context, status=404)


def server_error(request):
    """Custom 500 page"""
    context = {
        'error_code': '500',
        'error_title': 'Server Error',
        'error_message': 'Something went wrong on our end. Please try again later.',
    }
    return render(request, 'site/error.html', context, status=500)

def test_404(request):
    """Test view to demonstrate 404 page"""
    return not_found(request)


@require_http_methods(["POST"])
def submit_comment(request, video_id):
    """Submit a comment for a video (AJAX)"""
    try:
        video = get_object_or_404(Video, id=video_id, is_active=True)
        
        # Create form with user data
        form = CommentForm(request.POST, user=request.user)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.video = video
            comment.save()
            
            # Return success response with comment data
            return JsonResponse({
                'success': True,
                'message': 'Comment submitted successfully!',
                'comment': {
                    'id': comment.id,
                    'author_name': comment.author_name,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                    'is_guest': comment.user is None
                }
            })
        else:
            # Return form errors
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors[0] if field_errors else ''
            
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': errors
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while submitting the comment.',
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def toggle_like(request, video_id):
    """Toggle like for a video (AJAX)"""
    try:
        video = get_object_or_404(Video, id=video_id, is_active=True)
        
        # For now, we'll use a simple like counter
        # In a real application, you might want to track individual likes per user/IP
        video.likes += 1
        video.save(update_fields=['likes'])
        
        return JsonResponse({
            'success': True,
            'message': 'Video liked successfully!',
            'likes_count': video.likes
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while liking the video.',
            'error': str(e)
        }, status=500)


def cms_page(request, slug):
    """Display a CMS page"""
    try:
        cms_page = CMS.objects.get(slug=slug, is_active=True)
        context = {
            'cms_page': cms_page,
        }
        return render(request, 'site/cms_page.html', context)
    except CMS.DoesNotExist:
        return render(request, 'site/error.html', {'error_message': 'Page not found'}, status=404)


def verify_email(request, token):
    """Verify user email with token"""
    from core.models import User
    
    try:
        user = User.objects.get(email_verification_token=token)
        if user.verify_email(token):
            messages.success(request, 'Your account has been successfully activated! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid or expired activation link. Please request a new one.')
            return redirect('login')
    except User.DoesNotExist:
        messages.error(request, 'Invalid activation link.')
        return redirect('login')


@login_required(login_url='login')
def profile(request):
    """User profile page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        
        # Update user profile
        user = request.user
        user.name = name
        if email != user.email:
            # Email changed, need to verify new email
            user.email = email
            user.is_email_verified = False
            user.is_staff = False
            from core.utils import send_verification_email
            if send_verification_email(user, request):
                messages.success(request, 'Profile updated! Please check your new email and click the activation link.')
            else:
                messages.error(request, 'Profile updated but failed to send verification email.')
        else:
            user.save()
            messages.success(request, 'Profile updated successfully!')
        
        return redirect('profile')
    
    return render(request, 'site/profile.html')


@login_required(login_url='login')
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        user = request.user
        
        # Verify current password
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    
    return render(request, 'site/change_password.html')


@login_required(login_url='login')   
def resend_verification(request):
    """Resend email verification"""
    user = request.user
    if not user.is_email_verified:
        from core.utils import send_verification_email
        if send_verification_email(user, request):
            messages.success(request, 'Verification email sent! Please check your inbox.')
        else:
            messages.error(request, 'Failed to send verification email. Please try again later.')
    else:
        messages.info(request, 'Your email is already verified.')
    
    return redirect('profile')


def test_email(request):
    """Test email functionality for debugging"""
    if request.method == 'POST':
        test_email = request.POST.get('test_email')
        if test_email:
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                send_mail(
                    subject='Test Email from Adulto',
                    message='This is a test email to verify email configuration.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[test_email],
                    fail_silently=False,
                )
                messages.success(request, f'Test email sent successfully to {test_email}!')
            except Exception as e:
                messages.error(request, f'Failed to send test email: {str(e)}')
        else:
            messages.error(request, 'Please enter a valid email address.')
    
    return render(request, 'site/test_email.html')
