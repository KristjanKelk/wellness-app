# 🚀 Render Deployment Instructions for Wellness App

## 🔧 Immediate Fixes Applied

### 1. Fixed Redis Connection Issue
- **Problem**: `AbstractConnection.__init__() got an unexpected keyword argument 'connection_pool_kwargs'`
- **Solution**: Updated Redis configuration in `settings.py` to remove nested `connection_pool_kwargs`

### 2. Fixed Meal Planning API CORS Issues
- **Problem**: Requests to `http://localhost:8000/meal-planning/api/` being blocked
- **Solution**: Updated URL configuration to serve meal planning API at `/api/meal-planning/`

### 3. Added Robust Error Handling
- **Problem**: API crashes when Spoonacular API key is missing
- **Solution**: Added fallback meal plan generation and graceful error handling

## 🔑 Required Environment Variables for Render

Set these environment variables in your Render service settings:

### Required for Basic Functionality
```bash
# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=False

# Database (Render PostgreSQL)
PGDATABASE=your-database-name
PGUSER=your-database-user
PGPASSWORD=your-database-password
PGHOST=your-database-host
PGPORT=5432

# Redis (Render Redis) - Optional but recommended
REDIS_URL=redis://your-redis-url

# OpenAI API (for AI insights)
OPENAI_API_KEY=your-openai-api-key

# Spoonacular API (for meal planning)
SPOONACULAR_API_KEY=your-spoonacular-api-key
```

### Optional OAuth Variables
```bash
# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth (optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

## 📋 Step-by-Step Render Setup

### 1. Get Your API Keys

#### Spoonacular API Key (for meal planning)
1. Go to [spoonacular.com/food-api](https://spoonacular.com/food-api)
2. Sign up for a free account
3. Navigate to your dashboard
4. Copy your API key
5. **Free tier**: 150 requests/day

#### OpenAI API Key (for AI insights)
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up and add payment method
3. Go to API Keys section
4. Create a new API key
5. Copy the key

### 2. Update Render Environment Variables

In your Render dashboard:

1. Go to your service settings
2. Click "Environment" tab
3. Add each environment variable:

```bash
SECRET_KEY=django-insecure-your-secret-key-change-this-in-production
SPOONACULAR_API_KEY=your-actual-spoonacular-key-here
OPENAI_API_KEY=sk-your-actual-openai-key-here
PGDATABASE=wellness_app_db
PGUSER=your_postgres_user
PGPASSWORD=your_postgres_password
PGHOST=your-postgres-host.render.com
PGPORT=5432
REDIS_URL=redis://your-redis-url.render.com:6379
```

### 3. Test the Deployment

After deployment, test these endpoints:

#### Health Checks
```bash
# Main health check
curl https://your-app.onrender.com/api/health/

# Meal planning health check
curl https://your-app.onrender.com/api/meal-planning/health/
```

#### API Endpoints
```bash
# Nutrition profile (should work without API keys)
curl -H "Authorization: Bearer your-jwt-token" \
     https://your-app.onrender.com/api/meal-planning/nutrition-profile/current/

# Recipes (works with local database)
curl https://your-app.onrender.com/api/meal-planning/recipes/

# Meal plan generation (requires Spoonacular API key)
curl -X POST \
     -H "Authorization: Bearer your-jwt-token" \
     -H "Content-Type: application/json" \
     -d '{"plan_type":"daily","start_date":"2025-07-27"}' \
     https://your-app.onrender.com/api/meal-planning/meal-plans/generate/
```

## 🔍 Troubleshooting Guide

### Issue: "Meal planning service not configured"
**Cause**: Missing `SPOONACULAR_API_KEY` environment variable
**Solution**: 
1. Get API key from spoonacular.com
2. Add to Render environment variables
3. Redeploy service

### Issue: "Network Error" in frontend
**Cause**: CORS issues or wrong API URL
**Solution**: 
1. Verify frontend is using correct API URL: `https://your-app.onrender.com/api/`
2. Check browser console for specific CORS errors
3. Ensure backend is properly deployed

### Issue: "Throttling error: AbstractConnection"
**Cause**: Redis connection configuration issue (FIXED)
**Solution**: Already fixed in settings.py, redeploy if still seeing this

### Issue: 503 Service Unavailable
**Cause**: Service hibernation on free tier
**Solution**: 
1. Wait 30-60 seconds for service to wake up
2. Consider upgrading to paid plan
3. Use frontend's built-in retry logic

## 📊 Performance Expectations

### With API Keys Configured:
- ✅ Full meal planning functionality
- ✅ AI-generated meal plans
- ✅ Recipe recommendations
- ✅ Nutritional analysis

### Without API Keys (Fallback Mode):
- ✅ User nutrition profiles
- ✅ Manual meal logging
- ✅ Basic recipe browsing
- ❌ AI meal plan generation
- ❌ External recipe search

## 🚀 Deployment Commands

### Build Command (in Render)
```bash
pip install -r requirements.txt
```

### Start Command (in Render)
```bash
./start.sh
```

### Manual Migration (if needed)
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

## 🔐 Security Notes

1. **Never commit API keys** to your repository
2. **Use strong SECRET_KEY** in production
3. **Set DEBUG=False** in production
4. **Rotate API keys** periodically
5. **Monitor API usage** to avoid unexpected charges

## 📞 Support & Testing

### Test URLs After Deployment:
- Health Check: `https://your-app.onrender.com/api/health/`
- Meal Planning Health: `https://your-app.onrender.com/api/meal-planning/health/`
- API Root: `https://your-app.onrender.com/api/`

### Common Success Indicators:
- Health check returns `{"status": "healthy"}`
- Meal planning health shows API configuration status
- Frontend loads without CORS errors
- User registration works within 10 seconds

### Need Help?
1. Check Render logs for specific errors
2. Test health endpoints first
3. Verify environment variables are set
4. Ensure API keys are valid and have quota remaining

## 🎯 Quick Fix Summary

The main issues have been resolved:

1. ✅ **Redis connection fixed** - No more `AbstractConnection` errors
2. ✅ **CORS properly configured** - Frontend can access API
3. ✅ **URL structure fixed** - Meal planning at `/api/meal-planning/`
4. ✅ **Graceful fallbacks** - Works without external APIs
5. ✅ **Better error handling** - User-friendly error messages
6. ✅ **Health check endpoints** - Easy debugging

After setting the environment variables and redeploying, your meal planning features should work correctly!