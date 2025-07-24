#!/bin/bash

# Render startup script with enhanced error handling and Redis resilience

echo "🚀 Starting Wellness App with enhanced resilience..."

# Set error handling
set -e

# Function to check Redis connectivity
check_redis() {
    echo "🔍 Checking Redis connectivity..."
    if [ -n "$REDIS_URL" ]; then
        echo "   Redis URL configured: ${REDIS_URL:0:20}..."
        
        # Try to connect to Redis with timeout
        timeout 10s python -c "
import redis
import sys
import os
try:
    r = redis.from_url('$REDIS_URL', socket_timeout=5, socket_connect_timeout=5)
    r.ping()
    print('   ✅ Redis connection successful')
except Exception as e:
    print(f'   ⚠️  Redis connection failed: {e}')
    print('   ℹ️  App will use fallback cache - this is normal')
    sys.exit(0)  # Don't fail startup for Redis issues
" || echo "   ⚠️  Redis check timed out - using fallback"
    else
        echo "   ℹ️  Redis URL not configured, using local cache"
    fi
}

# Function to run database migrations safely
run_migrations() {
    echo "🔄 Running database migrations..."
    python manage.py migrate --noinput || {
        echo "❌ Migration failed, retrying once..."
        sleep 5
        python manage.py migrate --noinput
    }
    echo "✅ Migrations completed"
}

# Function to collect static files
collect_static() {
    echo "📦 Collecting static files..."
    python manage.py collectstatic --noinput --clear || {
        echo "⚠️  Static file collection failed, continuing..."
    }
}

# Function to run Redis diagnostics
run_diagnostics() {
    echo "🔍 Running system diagnostics..."
    python manage.py diagnose_redis || {
        echo "ℹ️  Diagnostics completed with warnings"
    }
}

# Main startup sequence
main() {
    echo "================================================"
    echo "🏥 Wellness App - Production Startup"
    echo "================================================"
    
    # Check Python environment
    echo "🐍 Python version: $(python --version)"
    echo "📍 Working directory: $(pwd)"
    
    # Install/check dependencies
    echo "📦 Checking dependencies..."
    pip install --quiet --no-cache-dir -r requirements.txt
    
    # System checks
    check_redis
    run_diagnostics
    
    # Database setup
    run_migrations
    
    # Static files
    collect_static
    
    # Final health check
    echo "🏥 Running final health check..."
    python -c "
from django.core.management import execute_from_command_line
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_project.settings')
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Database connection verified')
except Exception as e:
    print(f'❌ Database check failed: {e}')
    exit(1)
"
    
    echo "================================================"
    echo "🚀 Starting Gunicorn server..."
    echo "================================================"
    
    # Start the application with optimized settings
    exec gunicorn wellness_project.wsgi:application \
        --bind 0.0.0.0:${PORT:-10000} \
        --workers 2 \
        --worker-class sync \
        --worker-connections 1000 \
        --timeout 120 \
        --keep-alive 2 \
        --max-requests 1000 \
        --max-requests-jitter 50 \
        --preload \
        --access-logfile - \
        --error-logfile - \
        --log-level info
}

# Handle script interruption gracefully
trap 'echo "🛑 Startup interrupted"; exit 1' INT TERM

# Run main function
main "$@"