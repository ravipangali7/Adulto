from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Video, Category, Tag, CMS


class VideoSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Video.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.created_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6
    
    def items(self):
        return Category.objects.all()
    
    def lastmod(self, obj):
        return obj.videos.filter(is_active=True).order_by('-created_at').first().created_at if obj.videos.filter(is_active=True).exists() else None
    
    def location(self, obj):
        return reverse('categories') + f'?category={obj.slug}'


class TagSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    
    def items(self):
        return Tag.objects.all()
    
    def lastmod(self, obj):
        return obj.videos.filter(is_active=True).order_by('-created_at').first().created_at if obj.videos.filter(is_active=True).exists() else None
    
    def location(self, obj):
        return reverse('tags') + f'?tag={obj.slug}'


class CMSSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.4
    
    def items(self):
        return CMS.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class StaticSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9
    
    def items(self):
        return [
            'home',
            'videos',
            'categories',
            'tags',
            'latest',
            'popular',
        ]
    
    def location(self, item):
        return reverse(item)
