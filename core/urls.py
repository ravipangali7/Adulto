from django.urls import path
from django.contrib.sitemaps.views import sitemap
from . import views
from .sitemaps import VideoSitemap, CategorySitemap, TagSitemap, CMSSitemap, StaticSitemap

sitemaps = {
    'videos': VideoSitemap,
    'categories': CategorySitemap,
    'tags': TagSitemap,
    'cms': CMSSitemap,
    'static': StaticSitemap,
}

urlpatterns = [
	path('auth/login', views.login, name="auth_login"),
	path('dashboard', views.dashboard, name='dashboard'),

	# Category CRUD
	path('categories/', views.category_list, name='category_list'),
	path('categories/create/', views.category_create, name='category_create'),
	path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
	path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

	# Tag CRUD
	path('tags/', views.tag_list, name='tag_list'),
	path('tags/create/', views.tag_create, name='tag_create'),
	path('tags/<int:pk>/edit/', views.tag_update, name='tag_update'),
	path('tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),

	# Video CRUD
	path('videos/', views.video_list, name='video_list'),
	path('videos/create/', views.video_create, name='video_create'),
	path('videos/<int:pk>/edit/', views.video_update, name='video_update'),
	path('videos/<int:pk>/delete/', views.video_delete, name='video_delete'),
	path('videos/<int:pk>/toggle-status/', views.video_toggle_status, name='video_toggle_status'),

	# CMS CRUD
	path('cms/', views.cms_list, name='cms_list'),
	path('cms/create/', views.cms_create, name='cms_create'),
	path('cms/<int:pk>/edit/', views.cms_update, name='cms_update'),
	path('cms/<int:pk>/delete/', views.cms_delete, name='cms_delete'),
	path('cms/<slug:slug>/', views.cms_detail, name='cms_detail'),

	# Settings CRUD
	path('settings/', views.settings_list, name='settings_list'),
	path('settings/create/', views.settings_create, name='settings_create'),
	path('settings/<int:pk>/edit/', views.settings_update, name='settings_update'),
	path('settings/<int:pk>/delete/', views.settings_delete, name='settings_delete'),

	# Age Verification CRUD
	path('age-verification/', views.age_verification_list, name='age_verification_list'),
	path('age-verification/create/', views.age_verification_create, name='age_verification_create'),
	path('age-verification/<int:pk>/edit/', views.age_verification_update, name='age_verification_update'),
	path('age-verification/<int:pk>/delete/', views.age_verification_delete, name='age_verification_delete'),
	path('age-verification/<int:pk>/', views.age_verification_detail, name='age_verification_detail'),

	# User Management CRUD
	path('users/', views.user_list, name='user_list'),
	path('users/<int:pk>/', views.user_detail, name='user_detail'),
	path('users/<int:pk>/edit/', views.user_update, name='user_update'),
	path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

	# Sitemap
	path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

]
