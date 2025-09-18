"""
Google Analytics 4 API Service
Handles fetching data from Google Analytics 4 using the Reporting API
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    OrderBy,
    Filter,
    FilterExpression
)
from google.oauth2 import service_account
import logging

logger = logging.getLogger(__name__)

class GoogleAnalyticsService:
    """Service class for fetching Google Analytics 4 data"""
    
    def __init__(self):
        self.property_id = getattr(settings, 'GOOGLE_ANALYTICS_PROPERTY_ID', None)
        self.credentials_path = getattr(settings, 'GOOGLE_ANALYTICS_CREDENTIALS_PATH', None)
        self.client = None
        
        if self.property_id and self.credentials_path:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the GA4 client with service account credentials"""
        try:
            if os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                self.client = BetaAnalyticsDataClient(credentials=credentials)
                logger.info("Google Analytics client initialized successfully")
            else:
                logger.warning(f"GA4 credentials file not found at: {self.credentials_path}")
        except Exception as e:
            logger.error(f"Failed to initialize GA4 client: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if the service is properly configured and available"""
        return self.client is not None and self.property_id is not None
    
    def _run_report(self, dimensions: List[str], metrics: List[str], 
                   date_ranges: List[DateRange], 
                   order_by: Optional[List[OrderBy]] = None,
                   limit: Optional[int] = None) -> Dict[str, Any]:
        """Run a GA4 report and return the results"""
        if not self.is_available():
            return {}
        
        try:
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name=dim) for dim in dimensions],
                metrics=[Metric(name=metric) for metric in metrics],
                date_ranges=date_ranges,
                order_bys=order_by or [],
                limit=limit or 1000
            )
            
            response = self.client.run_report(request)
            
            # Process the response
            results = {
                'dimension_headers': [header.name for header in response.dimension_headers],
                'metric_headers': [header.name for header in response.metric_headers],
                'rows': []
            }
            
            for row in response.rows:
                row_data = {
                    'dimensions': [dim.value for dim in row.dimension_values],
                    'metrics': [float(met.value) for met in row.metric_values]
                }
                results['rows'].append(row_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error running GA4 report: {str(e)}")
            return {}
    
    def get_overview_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get overview statistics for the dashboard"""
        cache_key = f"ga4_overview_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return self._get_empty_overview()
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        # Get basic metrics
        metrics = ['sessions', 'totalUsers', 'screenPageViews', 'bounceRate']
        result = self._run_report([], metrics, [date_range])
        
        if not result or not result.get('rows'):
            return self._get_empty_overview()
        
        row = result['rows'][0]
        metrics_data = dict(zip(result['metric_headers'], row['metrics']))
        
        # Get previous period for comparison
        prev_start = start_date - timedelta(days=days)
        prev_end = start_date - timedelta(days=1)
        prev_date_range = DateRange(start_date=prev_start.strftime('%Y-%m-%d'), 
                                  end_date=prev_end.strftime('%Y-%m-%d'))
        
        prev_result = self._run_report([], metrics, [prev_date_range])
        prev_metrics = {}
        if prev_result and prev_result.get('rows'):
            prev_row = prev_result['rows'][0]
            prev_metrics = dict(zip(prev_result['metric_headers'], prev_row['metrics']))
        
        # Calculate percentage changes
        def calculate_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 1)
        
        overview_data = {
            'sessions': {
                'value': int(metrics_data.get('sessions', 0)),
                'change': calculate_change(metrics_data.get('sessions', 0), prev_metrics.get('sessions', 0))
            },
            'users': {
                'value': int(metrics_data.get('totalUsers', 0)),
                'change': calculate_change(metrics_data.get('totalUsers', 0), prev_metrics.get('totalUsers', 0))
            },
            'page_views': {
                'value': int(metrics_data.get('screenPageViews', 0)),
                'change': calculate_change(metrics_data.get('screenPageViews', 0), prev_metrics.get('screenPageViews', 0))
            },
            'bounce_rate': {
                'value': round(metrics_data.get('bounceRate', 0), 2),
                'change': calculate_change(metrics_data.get('bounceRate', 0), prev_metrics.get('bounceRate', 0))
            }
        }
        
        # Cache for 15 minutes
        cache.set(cache_key, overview_data, 900)
        return overview_data
    
    def get_traffic_sources(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get traffic sources data"""
        cache_key = f"ga4_traffic_sources_{days}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return []
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['sessionDefaultChannelGrouping']
        metrics = ['sessions', 'totalUsers']
        
        result = self._run_report(dimensions, metrics, [date_range], limit=limit)
        
        if not result or not result.get('rows'):
            return []
        
        traffic_sources = []
        for row in result['rows']:
            traffic_sources.append({
                'source': row['dimensions'][0],
                'sessions': int(row['metrics'][0]),
                'users': int(row['metrics'][1])
            })
        
        # Cache for 30 minutes
        cache.set(cache_key, traffic_sources, 1800)
        return traffic_sources
    
    def get_top_pages(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top pages by page views"""
        cache_key = f"ga4_top_pages_{days}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return []
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['pagePath', 'pageTitle']
        metrics = ['screenPageViews', 'sessions']
        
        order_by = [OrderBy(metric={'metric_name': 'screenPageViews'}, desc=True)]
        
        result = self._run_report(dimensions, metrics, [date_range], order_by=order_by, limit=limit)
        
        if not result or not result.get('rows'):
            return []
        
        top_pages = []
        for row in result['rows']:
            top_pages.append({
                'path': row['dimensions'][0],
                'title': row['dimensions'][1] or 'Untitled',
                'page_views': int(row['metrics'][0]),
                'sessions': int(row['metrics'][1])
            })
        
        # Cache for 30 minutes
        cache.set(cache_key, top_pages, 1800)
        return top_pages
    
    def get_geographic_data(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get geographic data (countries)"""
        cache_key = f"ga4_geographic_{days}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return []
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['country']
        metrics = ['sessions', 'totalUsers']
        
        order_by = [OrderBy(metric={'metric_name': 'sessions'}, desc=True)]
        
        result = self._run_report(dimensions, metrics, [date_range], order_by=order_by, limit=limit)
        
        if not result or not result.get('rows'):
            return []
        
        geographic_data = []
        for row in result['rows']:
            geographic_data.append({
                'country': row['dimensions'][0],
                'sessions': int(row['metrics'][0]),
                'users': int(row['metrics'][1])
            })
        
        # Cache for 1 hour
        cache.set(cache_key, geographic_data, 3600)
        return geographic_data
    
    def get_device_data(self, days: int = 7) -> Dict[str, Any]:
        """Get device category breakdown"""
        cache_key = f"ga4_device_data_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return {'desktop': 0, 'mobile': 0, 'tablet': 0}
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['deviceCategory']
        metrics = ['sessions']
        
        result = self._run_report(dimensions, metrics, [date_range])
        
        if not result or not result.get('rows'):
            return {'desktop': 0, 'mobile': 0, 'tablet': 0}
        
        device_data = {'desktop': 0, 'mobile': 0, 'tablet': 0}
        for row in result['rows']:
            device = row['dimensions'][0].lower()
            sessions = int(row['metrics'][0])
            if device in device_data:
                device_data[device] = sessions
        
        # Cache for 1 hour
        cache.set(cache_key, device_data, 3600)
        return device_data
    
    def get_daily_traffic(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily traffic data for charts"""
        cache_key = f"ga4_daily_traffic_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return []
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['date']
        metrics = ['sessions', 'totalUsers', 'screenPageViews']
        
        order_by = [OrderBy(dimension={'dimension_name': 'date'})]
        
        result = self._run_report(dimensions, metrics, [date_range], order_by=order_by)
        
        if not result or not result.get('rows'):
            return []
        
        daily_data = []
        for row in result['rows']:
            date_str = row['dimensions'][0]
            # Convert YYYYMMDD to readable format
            date_obj = datetime.strptime(date_str, '%Y%m%d').date()
            daily_data.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'sessions': int(row['metrics'][0]),
                'users': int(row['metrics'][1]),
                'page_views': int(row['metrics'][2])
            })
        
        # Cache for 30 minutes
        cache.set(cache_key, daily_data, 1800)
        return daily_data
    
    def get_detailed_traffic_sources(self, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """Get detailed traffic sources with more granular data"""
        cache_key = f"ga4_detailed_traffic_{days}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return []
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['sessionDefaultChannelGrouping', 'sessionSource', 'sessionMedium']
        metrics = ['sessions', 'totalUsers', 'screenPageViews', 'bounceRate']
        
        order_by = [OrderBy(metric={'metric_name': 'sessions'}, desc=True)]
        
        result = self._run_report(dimensions, metrics, [date_range], order_by=order_by, limit=limit)
        
        if not result or not result.get('rows'):
            return []
        
        traffic_sources = []
        for row in result['rows']:
            traffic_sources.append({
                'channel': row['dimensions'][0],
                'source': row['dimensions'][1],
                'medium': row['dimensions'][2],
                'sessions': int(row['metrics'][0]),
                'users': int(row['metrics'][1]),
                'page_views': int(row['metrics'][2]),
                'bounce_rate': round(float(row['metrics'][3]), 2)
            })
        
        # Cache for 30 minutes
        cache.set(cache_key, traffic_sources, 1800)
        return traffic_sources
    
    def get_events_data(self, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """Get events data"""
        cache_key = f"ga4_events_{days}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return []
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['eventName']
        metrics = ['eventCount', 'totalUsers']
        
        order_by = [OrderBy(metric={'metric_name': 'eventCount'}, desc=True)]
        
        result = self._run_report(dimensions, metrics, [date_range], order_by=order_by, limit=limit)
        
        if not result or not result.get('rows'):
            return []
        
        events_data = []
        for row in result['rows']:
            events_data.append({
                'event_name': row['dimensions'][0],
                'event_count': int(row['metrics'][0]),
                'unique_users': int(row['metrics'][1])
            })
        
        # Cache for 30 minutes
        cache.set(cache_key, events_data, 1800)
        return events_data
    
    def get_enhanced_geographic_data(self, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """Get enhanced geographic data with more details"""
        cache_key = f"ga4_enhanced_geo_{days}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return []
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['country', 'city', 'region']
        metrics = ['sessions', 'totalUsers', 'screenPageViews', 'bounceRate', 'averageSessionDuration']
        
        order_by = [OrderBy(metric={'metric_name': 'sessions'}, desc=True)]
        
        result = self._run_report(dimensions, metrics, [date_range], order_by=order_by, limit=limit)
        
        if not result or not result.get('rows'):
            return []
        
        geo_data = []
        for row in result['rows']:
            geo_data.append({
                'country': row['dimensions'][0],
                'city': row['dimensions'][1],
                'region': row['dimensions'][2],
                'sessions': int(row['metrics'][0]),
                'users': int(row['metrics'][1]),
                'page_views': int(row['metrics'][2]),
                'bounce_rate': round(float(row['metrics'][3]), 2),
                'avg_session_duration': round(float(row['metrics'][4]), 2)
            })
        
        # Cache for 1 hour
        cache.set(cache_key, geo_data, 3600)
        return geo_data
    
    def get_page_views_breakdown(self, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """Get detailed page views breakdown"""
        cache_key = f"ga4_page_views_{days}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if not self.is_available():
            return []
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        date_range = DateRange(start_date=start_date.strftime('%Y-%m-%d'), 
                              end_date=end_date.strftime('%Y-%m-%d'))
        
        dimensions = ['pagePath', 'pageTitle', 'landingPage']
        metrics = ['screenPageViews', 'sessions', 'totalUsers', 'bounceRate', 'averageSessionDuration']
        
        order_by = [OrderBy(metric={'metric_name': 'screenPageViews'}, desc=True)]
        
        result = self._run_report(dimensions, metrics, [date_range], order_by=order_by, limit=limit)
        
        if not result or not result.get('rows'):
            return []
        
        page_data = []
        for row in result['rows']:
            page_data.append({
                'path': row['dimensions'][0],
                'title': row['dimensions'][1] or 'Untitled',
                'landing_page': row['dimensions'][2],
                'page_views': int(row['metrics'][0]),
                'sessions': int(row['metrics'][1]),
                'users': int(row['metrics'][2]),
                'bounce_rate': round(float(row['metrics'][3]), 2),
                'avg_session_duration': round(float(row['metrics'][4]), 2)
            })
        
        # Cache for 30 minutes
        cache.set(cache_key, page_data, 1800)
        return page_data
    
    def _get_empty_overview(self) -> Dict[str, Any]:
        """Return empty overview data when GA4 is not available"""
        return {
            'sessions': {'value': 0, 'change': 0},
            'users': {'value': 0, 'change': 0},
            'page_views': {'value': 0, 'change': 0},
            'bounce_rate': {'value': 0, 'change': 0}
        }

# Global instance
ga_service = GoogleAnalyticsService()
