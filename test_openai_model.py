#!/usr/bin/env python
"""
Test script to verify OpenAI API connection with gpt-3.5-turbo model
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_project.settings')
django.setup()

from openai import OpenAI
from django.conf import settings

def test_openai_connection():
    """Test OpenAI API connection with gpt-3.5-turbo"""
    try:
        # Check if API key is set
        if not settings.OPENAI_API_KEY:
            print("❌ ERROR: OPENAI_API_KEY is not set in environment variables")
            return False
            
        print(f"✓ OpenAI API key found: {settings.OPENAI_API_KEY[:8]}...")
        
        # Initialize client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print("✓ OpenAI client initialized")
        
        # Test with gpt-3.5-turbo
        print("\nTesting gpt-3.5-turbo model...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, the API is working!' in exactly those words."}
            ],
            max_tokens=50,
            temperature=0
        )
        
        result = response.choices[0].message.content
        print(f"✓ Response received: {result}")
        
        if "Hello, the API is working!" in result:
            print("\n✅ SUCCESS: OpenAI API is working correctly with gpt-3.5-turbo!")
            return True
        else:
            print("\n⚠️  WARNING: Unexpected response from API")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing OpenAI API connection...")
    print("-" * 50)
    success = test_openai_connection()
    sys.exit(0 if success else 1)