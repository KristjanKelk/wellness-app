# CORS and Service Hibernation Fixes

## Issues Identified

### 1. CORS Configuration Problems
- **Domain Typo**: The frontend domain has a typo (`wellness-app-fronend.onrender.com` instead of `wellness-app-frontend.onrender.com`)
- **Conflicting CORS Settings**: `CORS_ALLOW_ALL_ORIGINS = True` was conflicting with specific allowed origins
- **Missing CORS Headers**: Some required headers were missing for proper API communication

### 2. Service Hibernation (Render.com Free Tier)
- **503 Errors**: Backend service goes to sleep after 15 minutes of inactivity
- **502 Errors**: Gateway errors during service startup
- **User Experience**: No feedback to users about service wake-up process

## Fixes Implemented

### 1. Backend CORS Configuration (`wellness_project/settings.py`)

```python
# Fixed CORS settings
CORS_ALLOW_ALL_ORIGINS = False  # Changed from True for better security

CORS_ALLOWED_ORIGINS = [
   'https://wellness-app-fronend.onrender.com',  # Keep typo version for compatibility
   'https://wellness-app-frontend.onrender.com',  # Correct spelling
   'https://wellness-app-tx2c.onrender.com',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]

# Updated allowed hosts
ALLOWED_HOSTS = [
    'wellness-app-tx2c.onrender.com',
    'wellness-app-frontend.onrender.com',
    'wellness-app-fronend.onrender.com',  # Keep typo version for compatibility
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

# Enhanced CORS headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma',
    'x-forwarded-for',
    'x-real-ip',
]

# Better middleware order
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Moved to top
    'django.middleware.security.SecurityMiddleware',
    # ... rest of middleware
]
```

### 2. Enhanced Error Handling (`frontend/src/services/http.service.js`)

```javascript
// Service hibernation handler
async function handleServiceHibernation(originalRequest) {
    console.log('Service appears to be hibernating. Attempting to wake up...');
    
    // Show user-friendly message
    if (store?.commit) {
        store.commit('ui/setLoading', {
            isLoading: true,
            message: 'Waking up service... This may take a minute on first load.'
        });
    }

    // Attempt to wake up service and retry
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    try {
        await axios.get(API_URL.replace('/api/', '/'), { timeout: 60000 });
        await new Promise(resolve => setTimeout(resolve, 3000));
        return apiClient(originalRequest);
    } catch (wakeupError) {
        return apiClient(originalRequest);
    }
}

// Enhanced interceptor with hibernation handling
apiClient.interceptors.response.use(
    response => response,
    async error => {
        // Handle service hibernation (503 errors)
        if (error.response?.status === 503 && !originalRequest._hibernation_retry) {
            originalRequest._hibernation_retry = true;
            return handleServiceHibernation(originalRequest);
        }

        // Handle 502 errors (bad gateway)
        if (error.response?.status === 502 && !originalRequest._gateway_retry) {
            originalRequest._gateway_retry = true;
            await new Promise(resolve => setTimeout(resolve, 5000));
            return apiClient(originalRequest);
        }
        
        // ... rest of error handling
    }
);
```

### 3. Service Wake-up Utilities (`frontend/src/utils/serviceWakeup.js`)

- **Service Health Check**: Monitor backend status
- **Wake-up Function**: Ping service to wake it from hibernation
- **Retry Logic**: Exponential backoff for failed requests
- **User Feedback**: Progress indicators during wake-up

### 4. User Interface Component (`frontend/src/components/ServiceStatus.vue`)

- **Status Modal**: Shows service wake-up progress
- **Progress Bar**: Visual feedback during wake-up
- **Error Handling**: User-friendly error messages
- **Educational Content**: Explains why wake-up is needed

### 5. Additional Debug Endpoints

```python
# Health check endpoint
@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Database connection test
        # CORS headers verification
        # Service status information

# CORS test endpoint
@method_decorator(csrf_exempt, name='dispatch')
class CorsTestView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({"message": "CORS test successful"})
    
    def post(self, request):
        return Response({"message": "CORS POST test successful"})
    
    def options(self, request):
        return Response({"message": "CORS OPTIONS test successful"})
```

## Testing the Fixes

### 1. Test CORS Configuration
```bash
# Test preflight request
curl -v -X OPTIONS \
  -H "Origin: https://wellness-app-fronend.onrender.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  https://wellness-app-tx2c.onrender.com/api/register/

# Test actual request
curl -v -X POST \
  -H "Origin: https://wellness-app-fronend.onrender.com" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"test123","password2":"test123"}' \
  https://wellness-app-tx2c.onrender.com/api/register/
```

### 2. Test Service Wake-up
```bash
# Check if service is hibernating
curl -v https://wellness-app-tx2c.onrender.com/

# Wake up service
curl -v https://wellness-app-tx2c.onrender.com/api/health/
```

## Deployment Notes

1. **Environment Variables**: Ensure all environment variables are set in Render.com
2. **Domain Configuration**: Verify correct domain names in both frontend and backend
3. **SSL/TLS**: HTTPS is required for CORS to work properly
4. **Service Monitoring**: Consider upgrading to paid plan to avoid hibernation

## Usage Instructions

### For Users
1. **First Load**: May take 30-60 seconds if service is sleeping
2. **Wait for Wake-up**: Don't refresh page during wake-up process
3. **Retry Button**: Use if initial connection fails

### For Developers
1. **Local Development**: Use localhost settings in development
2. **Production Deployment**: Ensure correct domain names
3. **Monitoring**: Check Render.com logs for issues
4. **Testing**: Use provided curl commands to verify CORS

## Common Issues and Solutions

### Issue: CORS errors persist
- **Solution**: Check domain names for typos
- **Solution**: Verify CORS middleware order
- **Solution**: Clear browser cache

### Issue: 503/502 errors
- **Solution**: Wait for service wake-up (30-60 seconds)
- **Solution**: Use retry logic in frontend
- **Solution**: Consider paid hosting plan

### Issue: Registration fails
- **Solution**: Check database connection
- **Solution**: Verify environment variables
- **Solution**: Check Django logs in Render.com

## Monitoring

- Use `curl` commands to test endpoints
- Check browser Network tab for CORS headers
- Monitor Render.com logs for backend issues
- Use health check endpoint for service status