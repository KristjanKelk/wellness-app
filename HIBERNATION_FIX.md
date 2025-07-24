# Service Hibernation & CORS Fix

## Problem Summary

Your wellness app is experiencing two interconnected issues:

1. **Service Hibernation**: Your backend service on Render.com (free tier) goes to sleep after 15 minutes of inactivity
2. **CORS Errors**: When the service is hibernating, it returns 503/502 errors instead of proper CORS headers

The error `Origin https://wellness-app-fronend.onrender.com is not allowed by Access-Control-Allow-Origin. Status code: 502` occurs because:
- The service is hibernating (returning 502/503)
- Hibernating services don't process Django middleware (including CORS)
- The browser sees this as a CORS violation

## Immediate Solutions

### 1. Wake Up Your Service Manually

Visit these URLs in your browser to wake up the backend:
- https://wellness-app-tx2c.onrender.com/
- https://wellness-app-tx2c.onrender.com/api/health/

Wait 30-60 seconds for the service to fully start, then try your registration again.

### 2. Frontend Changes (Already Implemented)

Your frontend now has enhanced hibernation handling in `frontend/src/services/http.service.js`:
- Detects hibernation errors (503/502)
- Automatically attempts to wake up the service
- Shows user-friendly messages during wake-up
- Retries requests after service is awake

### 3. Backend CORS Configuration (Fixed)

Updated `wellness_project/settings.py` with:
```python
# Temporarily allow all origins for debugging
CORS_ALLOW_ALL_ORIGINS = True

# Enhanced CORS headers
CORS_EXPOSE_HEADERS = [
    'content-type',
    'authorization',
    'x-csrftoken',
    'cache-control',
    'expires',
    'etag',
    'last-modified',
]
```

## Long-term Solutions

### Option 1: Upgrade to Paid Render Plan
- **Best Solution**: Upgrade to Render's paid plan ($7/month)
- No hibernation delays
- Better performance and reliability
- Professional deployment

### Option 2: Keep Service Active (Free Tier)
Use a service like UptimeRobot or similar to ping your service every 10 minutes:
- Ping URL: https://wellness-app-tx2c.onrender.com/api/health/
- Interval: Every 10 minutes
- This prevents hibernation

### Option 3: Service Warming on Frontend
Add this to your frontend's main.js or App.vue:

```javascript
// Service warming on app startup
import { initializeService } from './utils/serviceWakeup.js';

// On app mounted/created
async function warmUpService() {
    try {
        const success = await initializeService((message) => {
            console.log('Service warming:', message);
        });
        
        if (success) {
            console.log('Service is ready!');
        }
    } catch (error) {
        console.warn('Service warming failed:', error);
    }
}

// Call on app startup
warmUpService();
```

## Testing Your Fix

### Step 1: Manual Wake-up Test
1. Open https://wellness-app-tx2c.onrender.com/ in a new tab
2. Wait for any response (even 404 is OK)
3. Wait 30 seconds
4. Try your registration on the frontend

### Step 2: Automated Testing
```bash
# Test CORS after service is awake
curl -v -X OPTIONS \
  -H "Origin: https://wellness-app-fronend.onrender.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  https://wellness-app-tx2c.onrender.com/api/register/
```

You should see headers like:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: accept, accept-encoding, authorization, content-type, ...
```

## User Experience Improvements

### Show Loading States
Your frontend now shows users:
- "Service is starting up... This may take up to 60 seconds"
- Progress indicators during wake-up attempts
- Clear error messages if wake-up fails

### Error Handling
Enhanced error handling provides:
- Automatic retry logic
- User-friendly messages
- Graceful degradation

## Debugging Commands

If issues persist, use these commands:

```bash
# Check service status
curl -I https://wellness-app-tx2c.onrender.com/

# Test health endpoint
curl https://wellness-app-tx2c.onrender.com/api/health/

# Test CORS preflight
curl -v -X OPTIONS \
  -H "Origin: https://wellness-app-fronend.onrender.com" \
  -H "Access-Control-Request-Method: POST" \
  https://wellness-app-tx2c.onrender.com/api/register/
```

## Production Recommendations

### Security
Once hibernation is resolved, set:
```python
CORS_ALLOW_ALL_ORIGINS = False  # Better security
```

### Monitoring
- Set up uptime monitoring
- Monitor Render logs for errors
- Track wake-up frequency

### Performance
- Consider upgrading to paid tier
- Implement proper caching
- Use CDN for static assets

## Support

If you continue experiencing issues:
1. Check Render dashboard for service status
2. Review Render logs for errors
3. Verify environment variables are set
4. Consider contacting Render support

The hibernation is the root cause - once resolved, CORS will work perfectly!