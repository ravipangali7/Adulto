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
try:
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
    GOOGLE_ANALYTICS_AVAILABLE = True
except ImportError:
    GOOGLE_ANALYTICS_AVAILABLE = False
    # Create dummy classes for when GA is not available
    class BetaAnalyticsDataClient:
        pass
    class DateRange:
        pass
    class Dimension:
        pass
    class Metric:
        pass
    class RunReportRequest:
        pass
    class OrderBy:
        pass
    class Filter:
        pass
    class FilterExpression:
        pass
    class service_account:
        @staticmethod
        def Credentials():
            pass
import logging

logger = logging.getLogger(__name__)

class GoogleAnalyticsService:
    """Service class for fetching Google Analytics 4 data"""
    
    def __init__(self):
        self.property_id = getattr(settings, 'GOOGLE_ANALYTICS_PROPERTY_ID', None)
        self.credentials_path = getattr(settings, 'GOOGLE_ANALYTICS_CREDENTIALS_PATH', None)
        self.client = None
        
        # Initialize client if credentials are available
        if self.property_id and self.credentials_path and os.path.exists(self.credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                self.client = BetaAnalyticsDataClient(credentials=credentials)
            except Exception as e:
                logger.error(f"Failed to initialize Google Analytics client: {e}")
                self.client = None
    
    def _get_client(self):
        """Get or create the Analytics client"""
        if not GOOGLE_ANALYTICS_AVAILABLE:
            return None
            
        if not self.client:
            if not self.property_id or not self.credentials_path:
                return None
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                self.client = BetaAnalyticsDataClient(credentials=credentials)
            except Exception as e:
                logger.error(f"Failed to create Google Analytics client: {e}")
                return None
        return self.client
    
    def is_available(self):
        """Check if Google Analytics is available and configured"""
        return (
            GOOGLE_ANALYTICS_AVAILABLE and
            self.property_id is not None and 
            self.credentials_path is not None and 
            os.path.exists(self.credentials_path) and
            self._get_client() is not None
        )
    
    def get_overview_stats(self, days=7):
        """Get overview statistics for the dashboard"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return self._get_default_stats()
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="newUsers")
                ]
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Extract metrics
            if response.rows:
                row = response.rows[0]
                metrics = row.metric_values
                
                return {
                    'sessions': int(metrics[0].value) if metrics[0].value else 0,
                    'total_users': int(metrics[1].value) if metrics[1].value else 0,
                    'page_views': int(metrics[2].value) if metrics[2].value else 0,
                    'bounce_rate': float(metrics[3].value) if metrics[3].value else 0,
                    'avg_session_duration': float(metrics[4].value) if metrics[4].value else 0,
                    'new_users': int(metrics[5].value) if metrics[5].value else 0,
                }
            else:
                return self._get_default_stats()
                
        except Exception as e:
            logger.error(f"Error fetching overview stats: {e}")
            return self._get_default_stats()
    
    def get_page_views(self, days=30):
        """Get page views data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="date")],
                metrics=[Metric(name="screenPageViews")],
                order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))]
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                date_str = row.dimension_values[0].value
                page_views = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                data.append({
                    'date': date_str,
                    'page_views': page_views
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching page views: {e}")
            return []
    
    def get_top_pages(self, days=30, limit=10):
        """Get top pages by views"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="pagePath")],
                metrics=[Metric(name="screenPageViews")],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"))],
                limit=limit
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                page_path = row.dimension_values[0].value
                page_views = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                data.append({
                    'page_path': page_path,
                    'page_views': page_views
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching top pages: {e}")
            return []
    
    def get_traffic_sources(self, days=30, limit=10):
        """Get traffic sources data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="sessionSource")],
                metrics=[Metric(name="sessions")],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                source = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                data.append({
                    'source': source,
                    'sessions': sessions
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching traffic sources: {e}")
            return []
    
    def get_geographic_data(self, days=30, limit=10):
        """Get geographic data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="country")],
                metrics=[Metric(name="sessions")],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                country = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                data.append({
                    'country': country,
                    'sessions': sessions
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching geographic data: {e}")
            return []
    
    def get_device_data(self, days=30):
        """Get device data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return {
                    'desktop': 0,
                    'mobile': 0,
                    'tablet': 0
                }
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="deviceCategory")],
                metrics=[Metric(name="sessions")]
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            device_data = {
                'desktop': 0,
                'mobile': 0,
                'tablet': 0
            }
            
            for row in response.rows:
                device = row.dimension_values[0].value.lower()
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                if device in device_data:
                    device_data[device] = sessions
            
            return device_data
            
        except Exception as e:
            logger.error(f"Error fetching device data: {e}")
            return {
                'desktop': 0,
                'mobile': 0,
                'tablet': 0
            }
    
    def get_daily_traffic(self, days=30):
        """Get daily traffic data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="date")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))]
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                date_str = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'date': date_str,
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching daily traffic: {e}")
            return []
    
    def get_detailed_traffic_sources(self, days=30, limit=20):
        """Get detailed traffic sources data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium")
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="bounceRate")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                source = row.dimension_values[0].value
                medium = row.dimension_values[1].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                bounce_rate = float(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'source': source,
                    'medium': medium,
                    'sessions': sessions,
                    'users': users,
                    'bounce_rate': bounce_rate
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching detailed traffic sources: {e}")
            return []
    
    def get_page_views_breakdown(self, days=30, limit=20):
        """Get page views breakdown by page"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="pagePath")],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="sessions"),
                    Metric(name="averageSessionDuration")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"))],
                limit=limit
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                page_path = row.dimension_values[0].value
                page_views = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                sessions = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                avg_duration = float(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'page_path': page_path,
                    'page_views': page_views,
                    'sessions': sessions,
                    'avg_duration': avg_duration
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching page views breakdown: {e}")
            return []
    
    def get_enhanced_geographic_data(self, days=30, limit=20):
        """Get enhanced geographic data with more details"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[
                    Dimension(name="country"),
                    Dimension(name="city")
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                country = row.dimension_values[0].value
                city = row.dimension_values[1].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'country': country,
                    'city': city,
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching enhanced geographic data: {e}")
            return []
    
    def get_events_data(self, days=30, limit=20):
        """Get events data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Create date range
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Create request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="eventName")],
                metrics=[
                    Metric(name="eventCount"),
                    Metric(name="totalUsers")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"))],
                limit=limit
            )
            
            # Execute request
            response = client.run_report(request)
            
            # Process data
            data = []
            for row in response.rows:
                event_name = row.dimension_values[0].value
                event_count = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                data.append({
                    'event_name': event_name,
                    'event_count': event_count,
                    'users': users
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching events data: {e}")
            return []
    
    def _get_default_stats(self):
        """Return default stats when GA is not available"""
        return {
            'sessions': 0,
            'total_users': 0,
            'page_views': 0,
            'bounce_rate': 0.0,
            'avg_session_duration': 0.0,
            'new_users': 0,
        }

# Create instance
ga_service = GoogleAnalyticsService()