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

def _normalize_path(path: Optional[str]) -> Optional[str]:
    """
    Normalize a file path for cross-platform compatibility.
    - Convert empty strings to None
    - Convert relative paths to absolute paths relative to BASE_DIR
    - Normalize path separators (handles both / and \\ on Windows)
    """
    logger.debug(f"_normalize_path called with: {repr(path)}")
    
    if not path or not isinstance(path, str):
        logger.debug(f"_normalize_path: path is None or not string, returning None")
        return None
    
    # Strip whitespace
    path = path.strip()
    
    # Convert empty string to None
    if not path:
        logger.debug(f"_normalize_path: path is empty after strip, returning None")
        return None
    
    # Save original for logging
    original_path = path
    
    # Get BASE_DIR from settings first (needed for both absolute and relative paths)
    try:
        base_dir = getattr(settings, 'BASE_DIR', None)
        if not base_dir:
            # Try to get it from settings module directly
            from django.conf import settings as django_settings
            base_dir = getattr(django_settings, 'BASE_DIR', None)
    except Exception as e:
        logger.error(f"Error accessing BASE_DIR: {e}")
        base_dir = None
    
    # Check if path is absolute
    if os.path.isabs(path):
        normalized = os.path.normpath(path)
        if os.path.exists(normalized):
            logger.info(f"_normalize_path: Path is absolute and exists, using: '{normalized}'")
            return normalized
        else:
            # File doesn't exist at absolute path - ALWAYS try BASE_DIR first if available
            logger.warning(f"_normalize_path: Absolute path doesn't exist: '{normalized}'")
            if base_dir:
                # Extract filename and check if it exists in BASE_DIR
                filename = os.path.basename(normalized)
                try:
                    base_dir_str = str(base_dir.resolve()) if hasattr(base_dir, 'resolve') else str(base_dir)
                    base_dir_path = os.path.join(base_dir_str, filename)
                    if os.path.exists(base_dir_path):
                        logger.info(f"_normalize_path: Found file in BASE_DIR, using: '{base_dir_path}' instead of '{normalized}'")
                        return base_dir_path
                    else:
                        logger.info(f"_normalize_path: File not found in BASE_DIR either, will try relative resolution")
                        original_path = filename  # Use filename as relative path
                        # Fall through to BASE_DIR resolution below
                except Exception as e:
                    logger.error(f"_normalize_path: Error checking BASE_DIR: {e}")
                    original_path = os.path.basename(normalized)
                    # Fall through to BASE_DIR resolution below
            else:
                logger.error(f"_normalize_path: BASE_DIR not available, cannot resolve relative path")
                return normalized  # Return the absolute path even though it doesn't exist
    
    if base_dir:
        # Handle Path object from pathlib or string path
        if hasattr(base_dir, '__fspath__'):
            # Path object from pathlib (has __fspath__ method)
            base_dir_str = str(base_dir)
        elif hasattr(base_dir, 'resolve'):
            # Path object - convert using resolve() for absolute path
            base_dir_str = str(base_dir.resolve())
        elif isinstance(base_dir, (str, bytes)):
            # Already a string
            base_dir_str = str(base_dir)
        else:
            # Try to convert to string
            base_dir_str = str(base_dir)
        
        # Join paths properly - ensure base_dir_str is used
        if base_dir_str:
            # Use os.path.join to properly combine BASE_DIR with relative path
            resolved_path = os.path.join(base_dir_str, original_path)
            # Normalize the final path
            resolved_path = os.path.normpath(resolved_path)
            logger.info(f"Normalized relative path: '{original_path}' -> '{resolved_path}' (BASE_DIR: '{base_dir_str}')")
            return resolved_path
        else:
            logger.error(f"BASE_DIR converted to empty string, cannot resolve path: {original_path}")
            return None
    else:
        logger.error(f"BASE_DIR not found in settings, cannot resolve relative path: {original_path}")
        return None

class GoogleAnalyticsService:
    """Service class for fetching Google Analytics 4 data"""
    
    def __init__(self):
        self.client = None
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from settings and normalize values"""
        # Get property ID and handle empty strings
        property_id = getattr(settings, 'GOOGLE_ANALYTICS_PROPERTY_ID', None)
        if isinstance(property_id, str):
            property_id = property_id.strip() if property_id.strip() else None
        self.property_id = property_id
        
        # Get credentials path and normalize it
        credentials_path = getattr(settings, 'GOOGLE_ANALYTICS_CREDENTIALS_PATH', None)
        logger.info(f"Loading Google Analytics config - Raw credentials_path from settings: {repr(credentials_path)}")
        self.credentials_path = _normalize_path(credentials_path)
        logger.info(f"Loading Google Analytics config - Normalized credentials_path: {repr(self.credentials_path)}")
        
        # If normalized path doesn't exist, try to fix it by resolving filename relative to BASE_DIR
        if self.credentials_path and not os.path.exists(self.credentials_path):
            base_dir = getattr(settings, 'BASE_DIR', None)
            if base_dir:
                try:
                    base_dir_str = str(base_dir.resolve()) if hasattr(base_dir, 'resolve') else str(base_dir)
                    filename = os.path.basename(self.credentials_path)
                    fallback_path = os.path.join(base_dir_str, filename)
                    if os.path.exists(fallback_path):
                        logger.warning(f"Credentials file not found at normalized path: {self.credentials_path}")
                        logger.info(f"Found file at BASE_DIR location, using: {fallback_path}")
                        self.credentials_path = fallback_path
                except Exception as e:
                    logger.debug(f"Could not resolve fallback path: {e}")
        
        # Reset client to force re-initialization
        self.client = None
        
        # Initialize client if credentials are available
        if self.property_id and self.credentials_path and os.path.exists(self.credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                self.client = BetaAnalyticsDataClient(credentials=credentials)
                logger.info(f"Google Analytics client initialized successfully. Property ID: {self.property_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Google Analytics client: {e}", exc_info=True)
                self.client = None
        else:
            if not self.property_id:
                logger.debug("Google Analytics Property ID not configured")
            elif not self.credentials_path:
                logger.debug("Google Analytics credentials path not configured")
            elif not os.path.exists(self.credentials_path):
                # Check if file exists in BASE_DIR (common mistake: using absolute path instead of relative)
                base_dir = getattr(settings, 'BASE_DIR', None)
                if base_dir:
                    try:
                        base_dir_str = str(base_dir.resolve()) if hasattr(base_dir, 'resolve') else str(base_dir)
                        filename = os.path.basename(self.credentials_path)
                        suggested_path = os.path.join(base_dir_str, filename)
                        if os.path.exists(suggested_path):
                            logger.warning(f"Google Analytics credentials file not found at: {self.credentials_path}")
                            logger.warning(f"However, file exists at: {suggested_path}")
                            logger.warning(f"Hint: Set GOOGLE_ANALYTICS_CREDENTIALS_PATH to '{filename}' (relative path) instead of absolute path")
                        else:
                            logger.warning(f"Google Analytics credentials file not found: {self.credentials_path}")
                    except Exception:
                        logger.warning(f"Google Analytics credentials file not found: {self.credentials_path}")
                else:
                    logger.warning(f"Google Analytics credentials file not found: {self.credentials_path}")
    
    def reload_configuration(self):
        """Reload configuration from settings (useful when environment variables change)"""
        logger.info("Reloading Google Analytics configuration")
        self._load_configuration()
    
    def _get_client(self):
        """Get or create the Analytics client"""
        if not GOOGLE_ANALYTICS_AVAILABLE:
            logger.debug("Google Analytics libraries not available")
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
                logger.debug("Google Analytics client created successfully")
            except Exception as e:
                logger.error(f"Failed to create Google Analytics client: {e}", exc_info=True)
                return None
        return self.client
    
    def is_available(self):
        """Check if Google Analytics is available and configured"""
        checks = {
            'libraries_available': False,
            'property_id_configured': False,
            'credentials_path_configured': False,
            'credentials_file_exists': False,
            'client_initialized': False
        }
        
        # Check if libraries are available
        if not GOOGLE_ANALYTICS_AVAILABLE:
            logger.debug("Google Analytics check: Libraries not available")
            return False
        checks['libraries_available'] = True
        
        # Check property ID (handle empty strings)
        if not self.property_id or (isinstance(self.property_id, str) and not self.property_id.strip()):
            logger.debug("Google Analytics check: Property ID not configured or empty")
            return False
        checks['property_id_configured'] = True
        
        # Check credentials path
        if not self.credentials_path:
            logger.debug("Google Analytics check: Credentials path not configured")
            return False
        checks['credentials_path_configured'] = True
        
        # Check if file exists
        if not os.path.exists(self.credentials_path):
            logger.warning(f"Google Analytics check: Credentials file does not exist: {self.credentials_path}")
            return False
        checks['credentials_file_exists'] = True
        
        # Try to get client
        client = self._get_client()
        if not client:
            logger.debug("Google Analytics check: Client initialization failed")
            return False
        checks['client_initialized'] = True
        
        # All checks passed
        logger.debug(f"Google Analytics check: All checks passed. Status: {checks}")
        return True
    
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
    
    def get_browser_data(self, days=30, limit=20):
        """Get browser breakdown data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="browser")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                browser = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'browser': browser,
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching browser data: {e}")
            return []
    
    def get_os_data(self, days=30, limit=20):
        """Get operating system breakdown data"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="operatingSystem")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                os_name = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'os': os_name,
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching OS data: {e}")
            return []
    
    def get_technology_data(self, days=30, limit=30):
        """Get combined technology data (browser, OS, device)"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[
                    Dimension(name="browser"),
                    Dimension(name="operatingSystem"),
                    Dimension(name="deviceCategory")
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                browser = row.dimension_values[0].value
                os = row.dimension_values[1].value
                device = row.dimension_values[2].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'browser': browser,
                    'os': os,
                    'device': device,
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching technology data: {e}")
            return []
    
    def get_screen_resolution_data(self, days=30, limit=20):
        """Get screen resolution breakdown"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="screenResolution")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                resolution = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                data.append({
                    'resolution': resolution,
                    'sessions': sessions,
                    'users': users
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching screen resolution data: {e}")
            return []
    
    def get_mobile_device_info(self, days=30, limit=20):
        """Get mobile device information"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[
                    Dimension(name="mobileDeviceBranding"),
                    Dimension(name="mobileDeviceModel")
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                brand = row.dimension_values[0].value
                model = row.dimension_values[1].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                data.append({
                    'brand': brand,
                    'model': model,
                    'sessions': sessions,
                    'users': users
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching mobile device info: {e}")
            return []
    
    def get_hourly_traffic(self, days=7):
        """Get hourly traffic patterns"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="hour")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"))]
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                hour = int(row.dimension_values[0].value) if row.dimension_values[0].value else 0
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'hour': hour,
                    'hour_label': f"{hour:02d}:00",
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching hourly traffic: {e}")
            return []
    
    def get_weekly_patterns(self, days=30):
        """Get day of week traffic patterns"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="dayOfWeek")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="dayOfWeek"))]
            )
            
            response = client.run_report(request)
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            data = []
            for row in response.rows:
                day_num = int(row.dimension_values[0].value) if row.dimension_values[0].value else 0
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'day': day_num,
                    'day_name': day_names[day_num] if day_num < len(day_names) else f"Day {day_num}",
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views
                })
            
            return sorted(data, key=lambda x: x['day'])
        except Exception as e:
            logger.error(f"Error fetching weekly patterns: {e}")
            return []
    
    def get_new_vs_returning_users(self, days=30):
        """Get new vs returning users breakdown"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return {'new_users': 0, 'returning_users': 0}
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="newVsReturning")],
                metrics=[
                    Metric(name="totalUsers"),
                    Metric(name="sessions")
                ]
            )
            
            response = client.run_report(request)
            result = {'new_users': 0, 'returning_users': 0, 'new_sessions': 0, 'returning_sessions': 0}
            
            for row in response.rows:
                user_type = row.dimension_values[0].value
                users = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                sessions = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                
                if user_type == 'New Visitor':
                    result['new_users'] = users
                    result['new_sessions'] = sessions
                elif user_type == 'Returning Visitor':
                    result['returning_users'] = users
                    result['returning_sessions'] = sessions
            
            total_users = result['new_users'] + result['returning_users']
            result['new_users_percent'] = (result['new_users'] / total_users * 100) if total_users > 0 else 0
            result['returning_users_percent'] = (result['returning_users'] / total_users * 100) if total_users > 0 else 0
            
            return result
        except Exception as e:
            logger.error(f"Error fetching new vs returning users: {e}")
            return {'new_users': 0, 'returning_users': 0}
    
    def get_user_acquisition_channels(self, days=30, limit=20):
        """Get user acquisition channel grouping"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="sessionDefaultChannelGroup")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="newUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="bounceRate")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                channel = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                new_users = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                page_views = int(row.metric_values[3].value) if row.metric_values[3].value else 0
                bounce_rate = float(row.metric_values[4].value) if row.metric_values[4].value else 0
                data.append({
                    'channel': channel,
                    'sessions': sessions,
                    'users': users,
                    'new_users': new_users,
                    'page_views': page_views,
                    'bounce_rate': bounce_rate
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching acquisition channels: {e}")
            return []
    
    def get_landing_pages(self, days=30, limit=20):
        """Get landing pages analysis"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="landingPagePlusQueryString")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="bounceRate")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                page = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                avg_duration = float(row.metric_values[3].value) if row.metric_values[3].value else 0
                bounce_rate = float(row.metric_values[4].value) if row.metric_values[4].value else 0
                data.append({
                    'page': page,
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views,
                    'avg_duration': avg_duration,
                    'bounce_rate': bounce_rate
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching landing pages: {e}")
            return []
    
    def get_exit_pages(self, days=30, limit=20):
        """Get exit pages analysis"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="exitPage")],
                metrics=[
                    Metric(name="exits"),
                    Metric(name="screenPageViews"),
                    Metric(name="averageSessionDuration")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="exits"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                page = row.dimension_values[0].value
                exits = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                page_views = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                avg_duration = float(row.metric_values[2].value) if row.metric_values[2].value else 0
                exit_rate = (exits / page_views * 100) if page_views > 0 else 0
                data.append({
                    'page': page,
                    'exits': exits,
                    'page_views': page_views,
                    'exit_rate': exit_rate,
                    'avg_duration': avg_duration
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching exit pages: {e}")
            return []
    
    def get_referral_sources(self, days=30, limit=20):
        """Get external referral sources"""
        try:
            client = self._get_client()
            if not client or not self.property_id:
                return []
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            date_range = DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[Dimension(name="sessionSource")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"))],
                limit=limit
            )
            
            response = client.run_report(request)
            data = []
            for row in response.rows:
                source = row.dimension_values[0].value
                sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
                users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
                page_views = int(row.metric_values[2].value) if row.metric_values[2].value else 0
                data.append({
                    'source': source,
                    'sessions': sessions,
                    'users': users,
                    'page_views': page_views
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching referral sources: {e}")
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