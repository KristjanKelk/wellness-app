#!/usr/bin/env python3
"""
Setup script for Spoonacular API integration
This script helps configure and test Spoonacular API connection
"""

import os
import requests
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has SPOONACULAR_API_KEY"""
    env_files = ['.env', '.env.local']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
                if 'SPOONACULAR_API_KEY' in content:
                    # Extract the key value
                    for line in content.split('\n'):
                        if line.startswith('SPOONACULAR_API_KEY'):
                            key = line.split('=', 1)[1].strip().strip('"').strip("'")
                            if key and key != 'your_api_key_here':
                                return key
    return None

def test_spoonacular_api(api_key):
    """Test if Spoonacular API key works"""
    try:
        url = f"https://api.spoonacular.com/recipes/complexSearch"
        params = {
            'apiKey': api_key,
            'number': 1,
            'query': 'pasta'
        }
        
        print("🔍 Testing Spoonacular API...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total_results = data.get('totalResults', 0)
            print(f"✅ Spoonacular API is working! Found {total_results} pasta recipes.")
            return True
        elif response.status_code == 401:
            print("❌ Invalid API key. Please check your Spoonacular API key.")
            return False
        elif response.status_code == 402:
            print("❌ API quota exceeded. You've used all your free requests for today.")
            return False
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error testing API: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def setup_env_file(api_key):
    """Add API key to .env file"""
    env_file = '.env'
    
    # Read existing content
    content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
    
    # Check if SPOONACULAR_API_KEY already exists
    lines = content.split('\n')
    new_lines = []
    found = False
    
    for line in lines:
        if line.startswith('SPOONACULAR_API_KEY'):
            new_lines.append(f'SPOONACULAR_API_KEY={api_key}')
            found = True
        else:
            new_lines.append(line)
    
    # Add if not found
    if not found:
        new_lines.append(f'SPOONACULAR_API_KEY={api_key}')
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print(f"✅ API key added to {env_file}")

def get_free_api_key_instructions():
    """Provide instructions for getting a free API key"""
    print("\n📋 HOW TO GET A FREE SPOONACULAR API KEY:")
    print("="*50)
    print("1. Visit: https://spoonacular.com/food-api/console#Dashboard")
    print("2. Click 'Start Now' or 'Get API Key'")
    print("3. Create a free account")
    print("4. Verify your email address")
    print("5. Go to your dashboard and copy your API key")
    print("6. Free tier includes 150 requests per day")
    print("\n💡 The API key looks like: a1b2c3d4e5f6g7h8i9j0")

def main():
    print("🥗 Spoonacular API Setup for Wellness App")
    print("="*45)
    
    # Check if API key already exists
    existing_key = check_env_file()
    
    if existing_key:
        print(f"📍 Found existing API key: {existing_key[:8]}...")
        if test_spoonacular_api(existing_key):
            print("🎉 Your Spoonacular API is already configured and working!")
            print("\nYour meal planning app should now be able to:")
            print("- Fetch recipes from Spoonacular")
            print("- Search for recipes by ingredients")
            print("- Generate meal plans")
            return
        else:
            print("⚠️  Existing API key is not working.")
    
    # Prompt for new API key
    print("\n🔑 Let's set up your Spoonacular API key...")
    
    # Check if user has an API key
    has_key = input("\nDo you already have a Spoonacular API key? (y/n): ").lower().strip()
    
    if has_key.startswith('n'):
        get_free_api_key_instructions()
        print("\nCome back and run this script again once you have your API key!")
        return
    
    # Get API key from user
    while True:
        api_key = input("\nEnter your Spoonacular API key: ").strip()
        
        if not api_key:
            print("❌ Please enter a valid API key")
            continue
            
        if len(api_key) < 10:
            print("❌ API key seems too short. Please check and try again.")
            continue
            
        # Test the API key
        if test_spoonacular_api(api_key):
            # Save to .env file
            setup_env_file(api_key)
            print("\n🎉 SUCCESS! Your Spoonacular API is now configured!")
            print("\nNext steps:")
            print("1. Restart your Django server: python manage.py runserver")
            print("2. Your meal planning app will now fetch real recipes!")
            print("3. Try searching for recipes in your frontend")
            break
        else:
            retry = input("\nWould you like to try a different API key? (y/n): ").lower().strip()
            if not retry.startswith('y'):
                break
    
    print("\n📚 ADDITIONAL SETUP:")
    print("- Run 'python manage.py populate_sample_recipes' for immediate testing")
    print("- Check MEAL_PLANNING_FIXES.md for complete setup instructions")

if __name__ == "__main__":
    main()