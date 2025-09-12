from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from app import views

def robots_txt(request):
    content = """User-agent: *
Allow: /

# Sitemap
Sitemap: https://yourdomain.com/sitemap.xml

# Disallow admin and private areas
Disallow: /admin/
Disallow: /dashboard/
Disallow: /auth/
Disallow: /media/private/

# Allow important pages
Allow: /videos/
Allow: /categories/
Allow: /tags/
Allow: /latest/
Allow: /popular/
Allow: /search/
Allow: /page/

# Crawl delay (optional)
Crawl-delay: 1"""
    return HttpResponse(content, content_type='text/plain')

urlpatterns = [
    path('system/', admin.site.urls),
    path('core/', include('core.urls')),
    path('', include('app.urls')),
    path('robots.txt', robots_txt),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers
handler404 = views.not_found
handler500 = views.server_error