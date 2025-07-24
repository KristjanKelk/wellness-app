import time
import redis
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from decouple import config


class Command(BaseCommand):
    help = 'Diagnose Redis connection issues and provide solutions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test Redis connection with different timeout settings',
        )
        parser.add_argument(
            '--show-config',
            action='store_true',
            help='Show current Redis configuration',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Redis Diagnostic Tool ===\n'))

        if options['show_config']:
            self.show_redis_config()

        if options['test_connection']:
            self.test_redis_connection()

        # Always run basic diagnostics
        self.run_basic_diagnostics()

    def show_redis_config(self):
        """Show current Redis configuration"""
        self.stdout.write(self.style.HTTP_INFO('Current Redis Configuration:'))
        
        redis_url = config("REDIS_URL", default="")
        self.stdout.write(f"REDIS_URL: {redis_url[:50]}..." if len(redis_url) > 50 else f"REDIS_URL: {redis_url}")
        
        # Show cache settings
        cache_config = settings.CACHES.get('default', {})
        self.stdout.write(f"Cache Backend: {cache_config.get('BACKEND')}")
        self.stdout.write(f"Cache Location: {cache_config.get('LOCATION', '')[:50]}...")
        self.stdout.write(f"Cache Timeout: {cache_config.get('TIMEOUT')}")
        
        if hasattr(settings, 'REDIS_CONNECTION_OPTIONS'):
            self.stdout.write("Redis Connection Options:")
            for key, value in settings.REDIS_CONNECTION_OPTIONS.items():
                self.stdout.write(f"  {key}: {value}")
        
        self.stdout.write("")

    def test_redis_connection(self):
        """Test Redis connection with different configurations"""
        self.stdout.write(self.style.HTTP_INFO('Testing Redis Connection:'))
        
        redis_url = config("REDIS_URL", default="")
        if not redis_url:
            self.stdout.write(self.style.ERROR("❌ REDIS_URL not configured"))
            return

        # Test 1: Basic connection
        try:
            r = redis.from_url(redis_url, socket_timeout=5, socket_connect_timeout=5)
            r.ping()
            self.stdout.write(self.style.SUCCESS("✅ Basic Redis connection successful"))
        except redis.exceptions.TimeoutError:
            self.stdout.write(self.style.ERROR("❌ Redis connection timeout (5s)"))
        except redis.exceptions.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f"❌ Redis connection error: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Redis error: {e}"))

        # Test 2: Django cache
        try:
            cache.set("test_key", "test_value", 30)
            result = cache.get("test_key")
            if result == "test_value":
                self.stdout.write(self.style.SUCCESS("✅ Django cache test successful"))
            else:
                self.stdout.write(self.style.ERROR("❌ Django cache test failed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Django cache error: {e}"))

        # Test 3: Performance test
        try:
            start_time = time.time()
            for i in range(10):
                cache.set(f"perf_test_{i}", f"value_{i}", 60)
                cache.get(f"perf_test_{i}")
            end_time = time.time()
            avg_time = (end_time - start_time) / 20  # 20 operations total
            
            if avg_time < 0.01:  # 10ms per operation
                self.stdout.write(self.style.SUCCESS(f"✅ Performance test passed: {avg_time:.4f}s avg"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Performance slow: {avg_time:.4f}s avg"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Performance test failed: {e}"))

        self.stdout.write("")

    def run_basic_diagnostics(self):
        """Run basic diagnostics and provide recommendations"""
        self.stdout.write(self.style.HTTP_INFO('Diagnostic Results & Recommendations:'))
        
        redis_url = config("REDIS_URL", default="")
        
        if not redis_url:
            self.stdout.write(self.style.ERROR("❌ Redis not configured"))
            self.stdout.write("   Recommendation: Add REDIS_URL to your environment variables")
            self.stdout.write("   The app will use local memory cache as fallback")
        else:
            self.stdout.write(self.style.SUCCESS("✅ Redis URL configured"))
            
            # Check if Redis is external service
            if "onrender.com" in redis_url or "heroku" in redis_url or "aws" in redis_url:
                self.stdout.write("   ℹ️  Using external Redis service")
                self.stdout.write("   Recommendation: Ensure Redis service is in same region as your app")
                self.stdout.write("   Consider upgrading Redis plan if timeouts persist")

        # Check current cache backend
        cache_backend = settings.CACHES.get('default', {}).get('BACKEND', '')
        if 'redis' in cache_backend.lower():
            self.stdout.write("   ✅ Redis cache backend active")
        else:
            self.stdout.write("   ⚠️  Using fallback cache backend")
            self.stdout.write("   This is normal when Redis is unavailable")

        self.stdout.write("\n" + self.style.HTTP_INFO('Quick Fixes for Common Issues:'))
        self.stdout.write("1. Render Redis timeout:")
        self.stdout.write("   - Upgrade to paid Redis plan")
        self.stdout.write("   - Ensure app and Redis are in same region")
        self.stdout.write("   - Use connection pooling (already configured)")
        
        self.stdout.write("\n2. For immediate relief:")
        self.stdout.write("   - App works without Redis (uses local cache)")
        self.stdout.write("   - Registration and core features remain functional")
        self.stdout.write("   - Only rate limiting may be less precise")
        
        self.stdout.write("\n3. Render Platform Settings:")
        self.stdout.write("   - Check Redis service status in Render dashboard")
        self.stdout.write("   - Verify REDIS_URL environment variable")
        self.stdout.write("   - Consider Redis connection limit (free tier: 30 connections)")

        self.stdout.write(f"\n{self.style.SUCCESS('✅ Diagnostic complete!')}")