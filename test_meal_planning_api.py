#!/usr/bin/env python3
"""
Test script for meal planning API functionality
Run this to verify that the fixes are working correctly
"""

import requests
import json
import sys
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/meal-planning/api/"

# Test credentials - update these with real credentials
TEST_USER = {
    "username": "testuser",
    "password": "testpass123"
}

class MealPlanningAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None

    def login(self):
        """Authenticate and get token"""
        try:
            # Try to login
            login_url = f"{BASE_URL}/api/token/"
            response = self.session.post(login_url, data=TEST_USER)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                print("✅ Successfully authenticated")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print("Note: You may need to create a test user first")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def test_cors(self):
        """Test CORS configuration"""
        try:
            # Make an OPTIONS request to test CORS
            response = self.session.options(f"{API_BASE}recipes/")
            
            if response.status_code in [200, 204]:
                print("✅ CORS configuration working")
                return True
            else:
                print(f"❌ CORS issue: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ CORS test error: {e}")
            return False

    def test_recipes_endpoint(self):
        """Test recipe listing endpoint"""
        try:
            response = self.session.get(f"{API_BASE}recipes/")
            
            if response.status_code == 200:
                data = response.json()
                recipe_count = len(data.get('results', []))
                print(f"✅ Recipes endpoint working - Found {recipe_count} recipes")
                
                if recipe_count == 0:
                    print("⚠️  No recipes found. Run 'python manage.py populate_sample_recipes'")
                
                return True
            else:
                print(f"❌ Recipes endpoint failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Recipes test error: {e}")
            return False

    def test_nutrition_profile(self):
        """Test nutrition profile endpoint"""
        try:
            response = self.session.get(f"{API_BASE}nutrition-profile/current/")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Nutrition profile endpoint working")
                print(f"   Target calories: {data.get('calorie_target', 'Not set')}")
                return True
            else:
                print(f"❌ Nutrition profile failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Nutrition profile test error: {e}")
            return False

    def test_recipe_search(self):
        """Test recipe search functionality"""
        try:
            search_data = {
                "query": "chicken",
                "dietary_preferences": ["high_protein"],
                "number": 5
            }
            
            response = self.session.post(
                f"{API_BASE}recipes/search/",
                json=search_data
            )
            
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get('results', []))
                source = data.get('source', 'unknown')
                print(f"✅ Recipe search working - Found {result_count} recipes from {source}")
                return True
            else:
                print(f"❌ Recipe search failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Recipe search test error: {e}")
            return False

    def test_meal_plans(self):
        """Test meal plans endpoint"""
        try:
            response = self.session.get(f"{API_BASE}meal-plans/")
            
            if response.status_code == 200:
                data = response.json()
                plan_count = len(data.get('results', []))
                print(f"✅ Meal plans endpoint working - Found {plan_count} meal plans")
                return True
            else:
                print(f"❌ Meal plans failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Meal plans test error: {e}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Meal Planning API Tests\n")
        
        tests = [
            ("Authentication", self.login),
            ("CORS Configuration", self.test_cors),
            ("Recipes Endpoint", self.test_recipes_endpoint),
            ("Nutrition Profile", self.test_nutrition_profile),
            ("Recipe Search", self.test_recipe_search),
            ("Meal Plans", self.test_meal_plans),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🔍 Testing {test_name}...")
            success = test_func()
            results.append((test_name, success))
        
        # Summary
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = 0
        for test_name, success in results:
            status = "PASS" if success else "FAIL"
            print(f"{test_name}: {status}")
            if success:
                passed += 1
        
        print(f"\nTotal: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("🎉 All tests passed! Your meal planning API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            
        return passed == len(results)


def main():
    print("Meal Planning API Test Suite")
    print("="*30)
    
    tester = MealPlanningAPITester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("1. Make sure Django server is running: python manage.py runserver")
        print("2. Create a test user if authentication failed")
        print("3. Run sample recipe command: python manage.py populate_sample_recipes")
        print("4. Check CORS settings in wellness_project/settings.py")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()