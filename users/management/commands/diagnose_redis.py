import redis
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache
from decouple import config


class Command(BaseCommand):
    help = 'Diagnose Redis connectivity and cache configuration'

    def handle(self, *args, **options):
        self.stdout.write("=== Redis Diagnostic Tool ===")
        
        # Check Redis URL configuration
        redis_url = config("REDIS_URL", default="")
        if redis_url:
            self.stdout.write(f"✅ Redis URL configured")
            self.stdout.write(f"   Redis URL configured: {redis_url[:20]}...")
        else:
            self.stdout.write("⚠️  Redis URL not configured")
            self.stdout.write("   Using local memory cache instead")
            return

        # Test direct Redis connection
        try:
            self.stdout.write("🔍 Testing direct Redis connection...")
            r = redis.from_url(
                redis_url,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            r.ping()
            self.stdout.write("   ✅ Direct Redis connection successful")
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = f"test_{int(time.time())}"
            r.set(test_key, test_value, ex=30)
            retrieved = r.get(test_key)
            if retrieved and retrieved.decode() == test_value:
                self.stdout.write("   ✅ Redis read/write operations working")
            else:
                self.stdout.write("   ⚠️  Redis read/write test failed")
                
        except redis.TimeoutError:
            self.stdout.write("   ❌ Redis connection timeout")
            self.stdout.write("   This is common on Render.com free tier")
        except redis.ConnectionError as e:
            self.stdout.write(f"   ❌ Redis connection error: {e}")
        except Exception as e:
            self.stdout.write(f"   ❌ Redis error: {e}")

        # Test Django cache framework
        try:
            self.stdout.write("🔍 Testing Django cache framework...")
            cache_key = "django_cache_test"
            cache_value = f"test_{int(time.time())}"
            cache.set(cache_key, cache_value, 30)
            retrieved = cache.get(cache_key)
            if retrieved == cache_value:
                self.stdout.write("   ✅ Django cache working properly")
            else:
                self.stdout.write("   ⚠️  Django cache test failed")
        except Exception as e:
            self.stdout.write(f"   ❌ Django cache error: {e}")

        # Check cache backend configuration
        self.stdout.write("\n📋 Cache Configuration:")
        cache_config = settings.CACHES.get('default', {})
        backend = cache_config.get('BACKEND', 'unknown')
        self.stdout.write(f"   Backend: {backend}")
        
        if 'redis' in backend.lower():
            self.stdout.write("   ✅ Redis cache backend active")
        else:
            self.stdout.write("   ℹ️  Using local memory cache (fallback)")

        # Recommendations
        self.stdout.write("\n🔧 Diagnostic Results & Recommendations:")
        self.stdout.write("1. Render Redis timeout:")
        self.stdout.write("   - Use connection pooling (already configured)")
        self.stdout.write("   - Ensure app and Redis are in same region") 
        self.stdout.write("   - Upgrade to paid Redis plan")
        self.stdout.write("2. For immediate relief:")
        self.stdout.write("   - App works without Redis (uses local cache)")
        self.stdout.write("   - Registration and core features remain functional")
        self.stdout.write("   - Only rate limiting may be less precise")
        self.stdout.write("3. Render Platform Settings:")
        self.stdout.write("   - Check Redis service status in Render dashboard")
        self.stdout.write("   - Verify REDIS_URL environment variable")
        self.stdout.write("   - Consider Redis connection limit (free tier: 30 connections)")

        self.stdout.write("\n✅ Diagnostic complete!")