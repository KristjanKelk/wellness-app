#!/usr/bin/env python
"""
Deployment script for Spoonacular integration
This script helps migrate from fallback recipes to Spoonacular integration
"""
import os
import sys
import subprocess
import time

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment...")
    
    # Check if Django is available
    try:
        import django
        print(f"✅ Django {django.VERSION} available")
    except ImportError:
        print("❌ Django not found. Please install dependencies first.")
        return False
    
    # Check for .env file
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found. Make sure SPOONACULAR_API_KEY is configured.")
    
    # Check for manage.py
    if os.path.exists('manage.py'):
        print("✅ Django project structure detected")
        return True
    else:
        print("❌ manage.py not found. Run from project root directory.")
        return False

def backup_database():
    """Create a database backup before migration"""
    print("💾 Creating database backup...")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_before_spoonacular_{timestamp}.json"
    
    success = run_command(
        f"python manage.py dumpdata meal_planning --indent 2 > {backup_file}",
        "Database backup"
    )
    
    if success:
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    return None

def run_migrations():
    """Run Django migrations"""
    return run_command("python manage.py migrate", "Database migrations")

def remove_fallback_recipes():
    """Remove fallback recipes and populate with Spoonacular recipes"""
    return run_command(
        "python manage.py populate_spoonacular_recipes --remove-fallbacks --limit 50",
        "Fallback recipe removal and Spoonacular population"
    )

def test_integration():
    """Test the Spoonacular integration"""
    return run_command(
        "python test_spoonacular_integration.py",
        "Spoonacular integration testing"
    )

def restart_services():
    """Restart application services"""
    print("🔄 Restarting services...")
    
    # Try common restart methods
    restart_commands = [
        "sudo systemctl restart gunicorn",
        "sudo systemctl restart nginx",
        "docker-compose restart",
        "supervisorctl restart all"
    ]
    
    restarted = False
    for cmd in restart_commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Restarted with: {cmd}")
                restarted = True
                break
        except:
            continue
    
    if not restarted:
        print("⚠️  Could not automatically restart services. Please restart manually.")
    
    return True

def main():
    """Main deployment process"""
    print("🚀 Spoonacular Integration Deployment")
    print("=" * 50)
    
    # Step 1: Environment check
    if not check_environment():
        print("\n❌ Environment check failed. Please fix issues before continuing.")
        return False
    
    # Step 2: Backup
    backup_file = backup_database()
    if not backup_file:
        response = input("\n⚠️  Backup failed. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Deployment cancelled.")
            return False
    
    # Step 3: Migrations
    if not run_migrations():
        print("\n❌ Migration failed. Deployment cancelled.")
        return False
    
    # Step 4: Recipe migration
    print("\n📝 This step will:")
    print("   - Remove fallback/placeholder recipes")
    print("   - Fetch real recipes from Spoonacular API")
    print("   - Save them to local database")
    
    response = input("\nProceed with recipe migration? (y/N): ")
    if response.lower() == 'y':
        if not remove_fallback_recipes():
            print("\n⚠️  Recipe migration encountered issues. Check logs.")
    else:
        print("⚠️  Recipe migration skipped. You can run it later with:")
        print("   python manage.py populate_spoonacular_recipes --remove-fallbacks")
    
    # Step 5: Testing
    print("\n🧪 Testing integration...")
    if not test_integration():
        print("⚠️  Some tests failed. Check test output for details.")
    
    # Step 6: Restart services
    restart_services()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Spoonacular Integration Deployment Complete!")
    print("\n📋 Summary of changes:")
    print("   ✅ Fixed custom calorie target handling")
    print("   ✅ Enhanced recipe search with Spoonacular API")
    print("   ✅ Improved meal plan generation")
    print("   ✅ Fixed Redis connection configuration")
    print("   ✅ Added fallback recipe management")
    
    print("\n🔗 New API endpoints:")
    print("   GET  /meal-planning/api/recipes/search_spoonacular/")
    print("   POST /meal-planning/api/recipes/search/ (enhanced)")
    print("   POST /meal-planning/api/meal-plans/generate/ (with custom calories)")
    
    print("\n📖 Documentation:")
    print("   See SPOONACULAR_INTEGRATION.md for detailed usage")
    
    if backup_file:
        print(f"\n💾 Backup available: {backup_file}")
    
    print("\n✅ Deployment successful!")
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed with error: {e}")
        sys.exit(1)