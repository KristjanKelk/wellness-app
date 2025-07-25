#!/usr/bin/env python3
"""
Django management command to wake up the service and perform health checks.
Useful for monitoring and testing the hibernation handling.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import requests
import time
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Wake up the service and perform comprehensive health checks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://wellness-app-tx2c.onrender.com',
            help='Base URL of the service to wake up'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=120,
            help='Timeout in seconds for wake-up attempts'
        )
        parser.add_argument(
            '--max-attempts',
            type=int,
            default=6,
            help='Maximum number of wake-up attempts'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=10,
            help='Initial delay between attempts in seconds'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('🚀 Starting Service Wake-up & Health Check'))
        self.stdout.write('=' * 60)
        
        # Run comprehensive health checks
        try:
            # 1. Local service health
            self.check_local_health()
            
            # 2. Wake up external service
            if options['url'] != 'localhost':
                self.wake_up_service(
                    url=options['url'],
                    timeout=options['timeout'],
                    max_attempts=options['max_attempts'],
                    delay=options['delay']
                )
            
            # 3. API endpoint tests
            self.test_api_endpoints(options['url'])
            
            # 4. Summary
            self.stdout.write(self.style.SUCCESS('\n✅ All health checks completed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Health check failed: {str(e)}'))
            raise CommandError(f'Service wake-up failed: {str(e)}')

    def check_local_health(self):
        """Check local Django service health"""
        self.stdout.write('\n🔍 Checking local service health...')
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            self.stdout.write('  ✅ Database connection: OK')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Database connection: {str(e)}'))
        
        # Cache check
        try:
            cache.set('health_check', 'ok', 30)
            result = cache.get('health_check')
            if result == 'ok':
                self.stdout.write('  ✅ Cache system: OK')
            else:
                self.stdout.write('  ⚠️  Cache system: Not responding properly')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Cache system: {str(e)}'))
        
        # Settings check
        debug_status = "ON" if settings.DEBUG else "OFF"
        self.stdout.write(f'  ℹ️  Debug mode: {debug_status}')
        self.stdout.write(f'  ℹ️  Allowed hosts: {settings.ALLOWED_HOSTS[:3]}...')
        
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            self.stdout.write('  ✅ Redis configured')
        else:
            self.stdout.write('  ⚠️  Redis not configured (using local cache)')

    def wake_up_service(self, url, timeout, max_attempts, delay):
        """Attempt to wake up the external service"""
        self.stdout.write(f'\n🔄 Attempting to wake up service at {url}...')
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'WellnessApp-WakeUp/1.0',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        for attempt in range(1, max_attempts + 1):
            self.stdout.write(f'  🔄 Attempt {attempt}/{max_attempts}...')
            start_time = time.time()
            
            try:
                # Try to wake up the root endpoint
                response = session.get(url + '/', timeout=timeout)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Service responded in {response_time:.2f}s (Status: {response.status_code})'
                        )
                    )
                    
                    # Wait a moment for full initialization
                    self.stdout.write('  ⏳ Waiting for service to fully initialize...')
                    time.sleep(3)
                    return True
                    
                elif response.status_code == 503:
                    self.stdout.write(f'  🔄 Service hibernating (503), continuing...')
                    
                else:
                    self.stdout.write(f'  ⚠️  Unexpected status: {response.status_code}')
                    
            except requests.exceptions.Timeout:
                self.stdout.write(f'  ⏰ Request timeout after {timeout}s')
                
            except requests.exceptions.RequestException as e:
                self.stdout.write(f'  ❌ Request failed: {str(e)}')
            
            # Wait before next attempt (with increasing delay)
            if attempt < max_attempts:
                wait_time = delay * attempt
                self.stdout.write(f'  ⏳ Waiting {wait_time}s before next attempt...')
                time.sleep(wait_time)
        
        # All attempts failed
        self.stdout.write(self.style.WARNING(f'  ⚠️  Failed to wake up service after {max_attempts} attempts'))
        return False

    def test_api_endpoints(self, base_url):
        """Test critical API endpoints"""
        self.stdout.write('\n🧪 Testing API endpoints...')
        
        endpoints = [
            ('/api/health/', 'Health Check'),
            ('/api/cors-test/', 'CORS Test'),
            ('/meal-planning/api/nutrition-profile/current/', 'Meal Planning API'),
        ]
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'WellnessApp-HealthCheck/1.0',
            'Accept': 'application/json'
        })
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = session.get(base_url + endpoint, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code in [200, 401, 403]:  # 401/403 are OK for authenticated endpoints
                    self.stdout.write(
                        f'  ✅ {name}: OK ({response.status_code}) - {response_time:.2f}s'
                    )
                    
                    if self.verbose and response.headers.get('content-type', '').startswith('application/json'):
                        try:
                            data = response.json()
                            self.stdout.write(f'     Response: {json.dumps(data, indent=2)[:200]}...')
                        except:
                            pass
                            
                elif response.status_code == 503:
                    self.stdout.write(f'  🔄 {name}: Service hibernating (503)')
                    
                else:
                    self.stdout.write(f'  ⚠️  {name}: {response.status_code} - {response_time:.2f}s')
                    
            except requests.exceptions.Timeout:
                self.stdout.write(f'  ⏰ {name}: Timeout')
                
            except requests.exceptions.RequestException as e:
                self.stdout.write(f'  ❌ {name}: {str(e)}')

    def style_output(self, message, style=''):
        """Helper to style output consistently"""
        if style == 'success':
            return self.style.SUCCESS(message)
        elif style == 'warning':
            return self.style.WARNING(message)
        elif style == 'error':
            return self.style.ERROR(message)
        else:
            return message