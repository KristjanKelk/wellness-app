#!/usr/bin/env python
"""
Debug script for AI Assistant deployment issues
Run this on production to check configuration
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_project.settings')
django.setup()

from django.conf import settings
from django.db import connection


def check_environment():
    """Check environment variables"""
    print("🔍 Checking Environment Variables:")
    print("-" * 50)
    
    # Check OpenAI API Key
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if api_key:
        print(f"✅ OPENAI_API_KEY is set (length: {len(api_key)})")
        print(f"   First 10 chars: {api_key[:10]}...")
    else:
        print("❌ OPENAI_API_KEY is NOT set")
    
    # Check Redis
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        print(f"✅ REDIS_URL is set: {redis_url[:30]}...")
    else:
        print("⚠️  REDIS_URL is not set (will use local cache)")
    
    print()


def check_database_tables():
    """Check if AI Assistant tables exist"""
    print("🔍 Checking Database Tables:")
    print("-" * 50)
    
    tables_to_check = [
        'ai_assistant_conversation',
        'ai_assistant_message', 
        'ai_assistant_userpreference'
    ]
    
    with connection.cursor() as cursor:
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, [table])
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"✅ Table '{table}' exists")
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   Row count: {count}")
            else:
                print(f"❌ Table '{table}' does NOT exist")
    
    print()


def check_installed_apps():
    """Check if ai_assistant is in INSTALLED_APPS"""
    print("🔍 Checking INSTALLED_APPS:")
    print("-" * 50)
    
    if 'ai_assistant' in settings.INSTALLED_APPS:
        print("✅ 'ai_assistant' is in INSTALLED_APPS")
    else:
        print("❌ 'ai_assistant' is NOT in INSTALLED_APPS")
    
    print()


def check_openai_connection():
    """Test OpenAI API connection"""
    print("🔍 Testing OpenAI API Connection:")
    print("-" * 50)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Try a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        
        print("✅ OpenAI API connection successful")
        print(f"   Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {str(e)}")
    
    print()


def check_migrations():
    """Check migration status"""
    print("🔍 Checking Migration Status:")
    print("-" * 50)
    
    from django.db.migrations.executor import MigrationExecutor
    from django.db import connections
    
    executor = MigrationExecutor(connections['default'])
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    
    ai_assistant_migrations = [m for m in plan if m[0].app_label == 'ai_assistant']
    
    if ai_assistant_migrations:
        print(f"❌ {len(ai_assistant_migrations)} pending AI Assistant migrations:")
        for migration, backwards in ai_assistant_migrations:
            print(f"   - {migration}")
    else:
        print("✅ All AI Assistant migrations are applied")
    
    print()


def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("🤖 AI ASSISTANT DEPLOYMENT DIAGNOSTICS")
    print("="*60 + "\n")
    
    check_environment()
    check_installed_apps()
    check_database_tables()
    check_migrations()
    check_openai_connection()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print("\nIf you see any ❌ marks above, those issues need to be fixed.")
    print("Run 'python manage.py migrate ai_assistant' to create missing tables.")
    print("Set OPENAI_API_KEY environment variable if missing.\n")


if __name__ == "__main__":
    main()