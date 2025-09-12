from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse


class SEOMiddleware(MiddlewareMixin):
    """
    Middleware to add SEO-friendly headers and optimize performance
    """
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add cache headers for static content
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
            response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
        else:
            # Cache dynamic content for shorter periods
            response['Cache-Control'] = 'public, max-age=300'  # 5 minutes
        
        # Add Vary header for better caching
        if 'Vary' not in response:
            response['Vary'] = 'Accept-Encoding'
        
        return response
