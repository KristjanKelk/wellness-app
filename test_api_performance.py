#!/usr/bin/env python3
"""
Test script to verify API performance improvements and timeout fixes
"""
import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(url, method='GET', data=None, timeout=30):
    """Test an API endpoint and measure response time"""
    print(f"\n🔍 Testing {method} {url}")
    start_time = time.time()
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=timeout)
        
        execution_time = time.time() - start_time
        
        print(f"⏱️  Response time: {execution_time:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        # Check for performance headers
        if 'X-Execution-Time' in response.headers:
            print(f"⚡ Server execution time: {response.headers['X-Execution-Time']}")
        if 'X-Timeout-Limit' in response.headers:
            print(f"⏰ Timeout limit: {response.headers['X-Timeout-Limit']}")
        
        if response.status_code == 200:
            print("✅ Success")
            try:
                data = response.json()
                if 'data' in data and isinstance(data['data'], dict):
                    print(f"📦 Response data keys: {list(data['data'].keys())}")
            except:
                pass
        else:
            print(f"❌ Error: {response.text[:200]}")
            
        return execution_time, response.status_code
        
    except requests.exceptions.Timeout:
        execution_time = time.time() - start_time
        print(f"⏱️  Timeout after: {execution_time:.2f}s")
        print("⏰ Request timed out")
        return execution_time, 408
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"⏱️  Failed after: {execution_time:.2f}s")
        print(f"❌ Error: {e}")
        return execution_time, 500

def main():
    print("🚀 Testing Wellness App API Performance")
    print("=" * 50)
    
    # Test basic health check
    test_endpoint(f"{BASE_URL}/")
    test_endpoint(f"{BASE_URL}/api/health/")
    
    # Test optimized endpoints
    endpoints_to_test = [
        # Health profile endpoint (the one that was timing out)
        f"{BASE_URL}/api/health-profiles/my_profile/",
        
        # Meal planning endpoints
        f"{BASE_URL}/meal-planning/api/nutrition-profile/",
        f"{BASE_URL}/meal-planning/api/recipes/",
        f"{BASE_URL}/meal-planning/api/meal-plans/",
        
        # Weight history (this was timing out)
        f"{BASE_URL}/api/weight-history/",
    ]
    
    results = []
    for endpoint in endpoints_to_test:
        time.sleep(1)  # Small delay between requests
        exec_time, status_code = test_endpoint(endpoint, timeout=15)
        results.append({
            'endpoint': endpoint,
            'time': exec_time,
            'status': status_code
        })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 50)
    
    total_time = 0
    success_count = 0
    timeout_count = 0
    
    for result in results:
        status_icon = "✅" if result['status'] == 200 else "❌" if result['status'] >= 400 else "⚠️"
        print(f"{status_icon} {result['endpoint']}")
        print(f"   ⏱️  {result['time']:.2f}s | Status: {result['status']}")
        
        total_time += result['time']
        if result['status'] == 200:
            success_count += 1
        elif result['status'] == 408:
            timeout_count += 1
    
    print(f"\n📈 RESULTS:")
    print(f"   Total endpoints tested: {len(results)}")
    print(f"   Successful responses: {success_count}")
    print(f"   Timeout count: {timeout_count}")
    print(f"   Average response time: {total_time/len(results):.2f}s")
    print(f"   Total test time: {total_time:.2f}s")
    
    if timeout_count == 0 and success_count > len(results) * 0.8:
        print("\n🎉 API performance looks good! No timeouts detected.")
    elif timeout_count > 0:
        print(f"\n⚠️  {timeout_count} endpoints still timing out - needs investigation")
    else:
        print(f"\n⚠️  Some endpoints returning errors - check logs")

if __name__ == "__main__":
    main()