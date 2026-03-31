from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('videos/', views.videos, name='videos'),
    path('video/<slug:slug>/', views.video_detail, name='video_detail'),
    path('stream/<int:video_id>/', views.stream_video, name='stream_video'),
    path('categories/', views.categories, name='categories'),
    path('tags/', views.tags, name='tags'),
    path('latest/', views.latest, name='latest'),
    path('popular/', views.popular, name='popular'),
    path('search/', views.search, name='search'),
    path('login/', views.login_view, name='login'),
    # path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('test-email/', views.test_email, name='test_email'),
    path('page/<slug:slug>/', views.cms_page, name='cms_page'),
    path('test-404/', views.test_404, name='test_404'),
    # Comment and like functionality
    path('video/<int:video_id>/comment/', views.submit_comment, name='submit_comment'),
    path('video/<int:video_id>/like/', views.toggle_like, name='toggle_like'),
    path('submit-dmca-report/', views.submit_dmca_report, name='submit_dmca_report'),
    # Catch-all pattern for 404 testing (must be last)
    path('<path:path>/', views.not_found, name='catch_all_404'),
]