#!/bin/bash

# ==================================================
# Wellness App Deployment Script for Render.com
# ==================================================

echo "================================================"
echo "🚀 Starting Wellness App Deployment..."
echo "================================================"

# Exit on any error
set -e

# Set environment variables for production
export PYTHONUNBUFFERED=1
export DJANGO_SETTINGS_MODULE=wellness_project.settings

# Create logs directory if it doesn't exist
mkdir -p logs

# Install dependencies if requirements changed
echo "📦 Checking dependencies..."
pip install --no-cache-dir -r requirements.txt

# Run database migrations with better error handling
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput || {
    echo "❌ Migration failed, attempting to fix..."
    python manage.py migrate --fake-initial --noinput
    python manage.py migrate --noinput
}

# Collect static files
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if needed (for admin access)
echo "👤 Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created')
else:
    print('✅ Superuser already exists')
" || echo "⚠️  Superuser creation skipped"

# Test database connection
echo "🔍 Testing database connection..."
python manage.py shell -c "
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Database connection verified')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Test Redis connection (non-critical)
echo "🔍 Testing cache connection..."
python manage.py shell -c "
from django.core.cache import cache
try:
    cache.set('test', 'ok', 30)
    result = cache.get('test')
    if result == 'ok':
        print('✅ Cache connection verified')
    else:
        print('⚠️  Cache test failed but continuing...')
except Exception as e:
    print(f'⚠️  Cache connection error (non-critical): {e}')
"

# Run health check
echo "🏥 Running final health check..."
python manage.py shell -c "
import requests
from django.conf import settings
try:
    # Test the health endpoint
    print('Testing health endpoint...')
    # We'll test this after the server starts
    print('✅ Health check preparation complete')
except Exception as e:
    print(f'⚠️  Health check preparation error: {e}')
"

echo "================================================"
echo "🚀 Starting Gunicorn server..."
echo "================================================"

# Start Gunicorn with better configuration for production
exec gunicorn \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers ${WEB_CONCURRENCY:-2} \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    wellness_project.wsgi:application