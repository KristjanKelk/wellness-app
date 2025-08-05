# AI Assistant Deployment Fix Guide

## Problem Summary
The AI Assistant feature is returning 500 Internal Server Error responses for all endpoints. The errors are occurring because:

1. **Missing Database Migrations**: The AI Assistant models (Conversation, Message, UserPreference) exist in the code but the database tables haven't been created.
2. **Missing Environment Variables**: The OpenAI API key might not be configured in the production environment.

## Solution Steps

### 1. Create and Apply Database Migrations

First, ensure you have access to the production server or deployment pipeline.

#### Local Development:
```bash
# Activate your virtual environment
source venv/bin/activate  # or your environment activation command

# Create migrations for ai_assistant app
python manage.py makemigrations ai_assistant

# Apply migrations
python manage.py migrate ai_assistant
```

#### Production Deployment (Render):
Add these commands to your build script or run them manually:

```bash
# In your build.sh or start.sh script, add:
python manage.py migrate ai_assistant
```

### 2. Set Environment Variables

Ensure the following environment variable is set in your Render dashboard:

```
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. Verify Database Tables

After migration, verify the tables exist:

```sql
-- Check if tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('ai_assistant_conversation', 'ai_assistant_message', 'ai_assistant_userpreference');
```

### 4. Migration File Created

I've already created the initial migration file at `/workspace/ai_assistant/migrations/0001_initial.py` with the following models:

- **Conversation**: Stores AI conversation sessions
- **Message**: Stores individual messages in conversations  
- **UserPreference**: Stores user preferences for AI responses

### 5. Deployment Checklist

Before deploying, ensure:

- [ ] All environment variables are set (especially `OPENAI_API_KEY`)
- [ ] Database migrations are run (`python manage.py migrate`)
- [ ] The PostgreSQL database is accessible
- [ ] The AI Assistant app is in INSTALLED_APPS (already confirmed ✓)
- [ ] URLs are properly configured (already confirmed ✓)

### 6. Test After Deployment

After applying fixes, test the endpoints:

```bash
# Test active conversation endpoint
curl -X GET https://wellness-app-tx2c.onrender.com/api/ai-assistant/conversations/active/ \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"

# Test preferences endpoint  
curl -X GET https://wellness-app-tx2c.onrender.com/api/ai-assistant/preferences/current/ \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
```

### 7. Common Issues and Solutions

**Issue**: Still getting 500 errors after migrations
- Check server logs for specific error messages
- Verify OpenAI API key is valid
- Check database connection settings

**Issue**: Migration fails
- Ensure PostgreSQL extensions are enabled (especially for JSONField)
- Check user permissions on the database

**Issue**: OpenAI API errors
- Verify API key has sufficient credits
- Check rate limits
- Ensure the key has access to the required models (gpt-4o-mini)

### 8. Emergency Rollback

If issues persist, you can temporarily disable the AI Assistant:

1. Comment out the AI Assistant URL include in `wellness_project/urls.py`
2. Remove 'ai_assistant' from INSTALLED_APPS
3. Redeploy

## Next Steps

1. Apply the migrations on your production database
2. Set the OPENAI_API_KEY environment variable
3. Restart the application
4. Monitor logs for any remaining issues

The AI Assistant should start working once these steps are completed.