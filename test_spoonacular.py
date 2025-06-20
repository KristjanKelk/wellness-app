# test_spoonacular.py (create this in your project root)
import os
import requests
from decouple import config

# Test Spoonacular API connection
api_key = config('SPOONACULAR_API_KEY')
url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey={api_key}&number=1"

try:
    response = requests.get(url)
    if response.status_code == 200:
        print("✅ Spoonacular API key works!")
        data = response.json()
        print(f"Found {data['totalResults']} recipes")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Connection Error: {e}")