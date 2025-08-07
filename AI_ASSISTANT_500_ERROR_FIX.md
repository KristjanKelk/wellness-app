# AI Assistant 500 Error Fix Guide

## Problem
The AI Assistant is returning a 500 Internal Server Error when trying to send messages via the endpoint:
```
POST https://wellness-app-tx2c.onrender.com/api/ai-assistant/conversations/send_message/
```

## Root Causes and Solutions

### 1. Missing or Invalid OpenAI API Key
**Symptoms:**
- 500 error on send_message endpoint
- Error message: "OpenAI API authentication failed"

**Solution:**
1. Check if OPENAI_API_KEY is set in your environment:
   ```bash
   echo $OPENAI_API_KEY
   ```

2. Add to your `.env` file:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. For Render deployment, add the environment variable in the Render dashboard:
   - Go to your service settings
   - Add environment variable: `OPENAI_API_KEY`

### 2. Database Migration Issues
**Symptoms:**
- UserPreference or Conversation models not found
- Database integrity errors

**Solution:**
```bash
# Run migrations
python manage.py migrate
python manage.py migrate ai_assistant

# Verify migrations
python manage.py showmigrations ai_assistant
```

### 3. Missing Dependencies
**Symptoms:**
- ImportError for openai or tiktoken
- Module not found errors

**Solution:**
```bash
# Install required packages
pip install openai==1.12.0
pip install tiktoken==0.5.2
pip install python-decouple==3.8

# Update requirements.txt
pip freeze > requirements.txt
```

### 4. Configuration Issues (Fixed in Code)
**What was fixed:**
- Removed duplicate OPENAI_API_KEY definition in settings.py
- Added proper error handling in ConversationManager
- Added OpenAI API error specific handling
- Improved error logging in views.py

## Quick Deployment Checklist

1. **Environment Variables**
   ```bash
   # Required in .env or Render environment
   OPENAI_API_KEY=sk-...
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgresql://...  # For production
   ```

2. **Run Deployment Check**
   ```bash
   python ai_assistant_deployment_check.py
   ```

3. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser  # If needed
   ```

4. **Test the API**
   ```bash
   # Test with curl
   curl -X POST https://your-app.onrender.com/api/ai-assistant/conversations/send_message/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-auth-token" \
     -d '{"message": "Hello", "conversation_id": null}'
   ```

## Debugging Steps

1. **Check Render Logs**
   ```bash
   # In Render dashboard, check service logs for specific errors
   ```

2. **Enable Debug Mode Temporarily**
   ```python
   # In settings.py (for debugging only!)
   DEBUG = True  # Remember to set back to False
   ```

3. **Test Locally**
   ```bash
   # Set up local environment
   export OPENAI_API_KEY=your-key
   python manage.py runserver
   # Test the endpoint locally
   ```

## Code Changes Made

1. **settings.py**: Removed duplicate OPENAI_API_KEY definition
2. **conversation_manager.py**: Added API key validation and better error handling
3. **views.py**: Added detailed error logging

## Prevention

1. Always test AI assistant after deployment:
   ```bash
   python manage.py test ai_assistant
   ```

2. Monitor API usage and limits in OpenAI dashboard

3. Set up proper logging:
   ```python
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'file': {
               'level': 'ERROR',
               'class': 'logging.FileHandler',
               'filename': 'ai_assistant_errors.log',
           },
       },
       'loggers': {
           'ai_assistant': {
               'handlers': ['file'],
               'level': 'ERROR',
               'propagate': True,
           },
       },
   }
   ```

## Next Steps

After applying these fixes:
1. Restart your Render service
2. Check the logs for any remaining errors
3. Test the endpoint again
4. If issues persist, check the specific error message in logs