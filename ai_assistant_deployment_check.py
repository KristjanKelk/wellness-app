#!/usr/bin/env python3
"""
AI Assistant Deployment Checklist
This script verifies that the AI assistant is properly configured for deployment.
"""

import os
import sys

def check_environment():
    """Check environment variables and configuration"""
    print("=== AI Assistant Deployment Checklist ===\n")
    
    issues = []
    warnings = []
    
    # Check for .env file
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("✅ .env file found")
    else:
        print("❌ .env file NOT found")
        issues.append("Create a .env file with required environment variables")
    
    # Check OpenAI API key
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key:
        print(f"✅ OPENAI_API_KEY is set (length: {len(openai_key)})")
    else:
        print("❌ OPENAI_API_KEY is NOT set")
        issues.append("Set OPENAI_API_KEY in your .env file")
    
    # Check database URL
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        print("✅ DATABASE_URL is set")
    else:
        print("⚠️  DATABASE_URL is NOT set (using SQLite)")
        warnings.append("Consider setting DATABASE_URL for production")
    
    # Check SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY', '')
    if secret_key and secret_key != 'django-insecure-default-key':
        print("✅ SECRET_KEY is properly set")
    else:
        print("❌ SECRET_KEY is NOT properly set")
        issues.append("Set a secure SECRET_KEY in your .env file")
    
    print("\n=== Deployment Steps ===")
    print("\n1. Environment Setup:")
    print("   - Copy .env.example to .env")
    print("   - Set OPENAI_API_KEY in .env file")
    print("   - Set other required variables")
    
    print("\n2. Database Setup:")
    print("   - Run: python manage.py migrate")
    print("   - Run: python manage.py migrate ai_assistant")
    
    print("\n3. Static Files:")
    print("   - Run: python manage.py collectstatic --noinput")
    
    print("\n4. Frontend Build:")
    print("   - cd frontend && npm install && npm run build")
    
    if issues:
        print(f"\n❌ Found {len(issues)} critical issues:")
        for issue in issues:
            print(f"   - {issue}")
    
    if warnings:
        print(f"\n⚠️  Found {len(warnings)} warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not issues:
        print("\n✅ All critical checks passed!")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)