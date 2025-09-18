# Google Analytics 4 Integration Setup Guide

This guide will help you set up Google Analytics 4 data integration in your Django dashboard.

## Prerequisites

1. A Google Analytics 4 property set up
2. A Google Cloud Project with Analytics Reporting API enabled
3. A service account with Analytics Viewer permissions

## Step 1: Install Dependencies

The required packages are already added to `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

## Step 2: Set Up Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Google Analytics Reporting API" for your project
4. Go to "IAM & Admin" > "Service Accounts"
5. Create a new service account:
   - Name: `analytics-dashboard-service`
   - Description: `Service account for dashboard analytics`
6. Grant the service account the "Viewer" role for your Analytics property
7. Create a JSON key for the service account and download it
8. Place the JSON key file in your project directory (e.g., `credentials/analytics-key.json`)

## Step 3: Get Your Analytics Property ID

1. Go to [Google Analytics](https://analytics.google.com/)
2. Select your property
3. Go to "Admin" > "Property Settings"
4. Copy the "Property ID" (it's a number like `123456789`)

## Step 4: Configure Environment Variables

Add these variables to your `.env` file:

```env
# Google Analytics Configuration
GOOGLE_ANALYTICS_TRACKING_ID=G-XXXXXXXXXX
GOOGLE_ANALYTICS_ENABLED=True

# Google Analytics 4 API Configuration
GOOGLE_ANALYTICS_PROPERTY_ID=123456789
GOOGLE_ANALYTICS_CREDENTIALS_PATH=/path/to/your/service-account-key.json
```

Replace:
- `G-XXXXXXXXXX` with your GA4 Measurement ID
- `123456789` with your Analytics Property ID
- `/path/to/your/service-account-key.json` with the actual path to your JSON key file

## Step 5: Grant Analytics Access

1. In Google Analytics, go to "Admin" > "Property Access Management"
2. Click the "+" button to add users
3. Add your service account email (found in the JSON key file)
4. Grant "Viewer" permissions

## Step 6: Test the Integration

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Go to your dashboard at `http://localhost:8000/dashboard/`

3. You should see:
   - Google Analytics overview cards at the top
   - Traffic sources chart
   - Device category chart
   - Top pages table
   - Geographic data table

## Troubleshooting

### No Data Showing
- Check that your service account has access to the Analytics property
- Verify the Property ID is correct
- Ensure the credentials file path is correct
- Check Django logs for any API errors

### API Errors
- Make sure the Analytics Reporting API is enabled in Google Cloud Console
- Verify the service account has the correct permissions
- Check that the JSON key file is valid and not corrupted

### Caching Issues
- The service caches data for performance (15-60 minutes)
- Clear cache if you need fresh data: `python manage.py shell` then `from django.core.cache import cache; cache.clear()`

## Features Included

The integration provides:

1. **Overview Statistics**: Sessions, Users, Page Views, Bounce Rate with period-over-period comparison
2. **Traffic Sources**: Breakdown by channel (Organic, Direct, Social, etc.)
3. **Top Pages**: Most viewed pages with page views and sessions
4. **Geographic Data**: Top countries by sessions and users
5. **Device Categories**: Desktop, Mobile, Tablet breakdown
6. **Daily Traffic**: Time series data for charts

## Security Notes

- Never commit your service account JSON key to version control
- Use environment variables for all sensitive configuration
- Consider using a secrets management service in production
- Regularly rotate your service account keys

## Performance

- Data is cached for 15-60 minutes to reduce API calls
- The service gracefully handles API failures
- Empty data states are handled with user-friendly messages
