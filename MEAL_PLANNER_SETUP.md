# 🍽️ Meal Planner Setup Guide

## Overview

This guide will help you set up the enhanced meal planning system with Spoonacular API integration, providing access to thousands of real recipes and AI-powered meal plan generation.

## ✨ New Features

- **Spoonacular Integration**: Access to 330,000+ real recipes
- **Smart Recipe Search**: Toggle between local and Spoonacular databases
- **Enhanced Recipe Browser**: Improved UI with search filters
- **AI Meal Planning**: Generate personalized meal plans
- **Real-time Recipe Loading**: Load more recipes as you scroll

## 🚀 Quick Setup

### 1. Environment Setup

Add your Spoonacular API key to `.env.local`:

```bash
# Get a free API key from https://spoonacular.com/food-api
SPOONACULAR_API_KEY=your_actual_api_key_here
```

### 2. Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Database Setup

```bash
# Apply migrations
python manage.py migrate

# Run the automated setup script
python setup_spoonacular.py
```

### 4. Start Services

```bash
# Terminal 1: Start Django backend
python manage.py runserver

# Terminal 2: Start Vue frontend
cd frontend
npm run serve
```

### 5. Access the Application

Open your browser to:
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000

## 📖 Detailed Setup Instructions

### Getting a Spoonacular API Key

1. Visit [Spoonacular Food API](https://spoonacular.com/food-api)
2. Click "Get Started" and sign up for a free account
3. After registration, go to your dashboard
4. Copy your API key from the "Your API Key" section
5. The free tier includes 150 requests per day

### Environment Configuration

Create or update your `.env.local` file:

```bash
# Django settings
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

# API Keys
SPOONACULAR_API_KEY=your_spoonacular_api_key_here

# Frontend
VUE_APP_API_URL=http://localhost:8000/api
```

### Frontend Build (Production)

```bash
cd frontend
npm run build
cd ..
python manage.py collectstatic --noinput
```

## 🔧 Features Guide

### Recipe Browser

1. **Local Recipes**: Browse recipes stored in your database
2. **Spoonacular Search**: Search the global recipe database
3. **Filters**: Filter by cuisine, meal type, and dietary preferences
4. **Load More**: Automatically load additional recipes

### Meal Planning

1. **Profile Setup**: Configure your nutrition profile first
2. **Generate Plans**: Create AI-powered meal plans
3. **View Details**: Click on meal plans to see full details
4. **Regenerate**: Create new variations of existing plans

### Navigation

- **Recipes Tab**: Browse and search recipes
- **Profile Tab**: Set up your nutrition preferences
- **Meal Plans Tab**: Generate and manage meal plans
- **Analytics Tab**: View nutrition analytics (coming soon)

## 🐛 Troubleshooting

### Common Issues

**"No recipes showing"**
- Check if Spoonacular API key is configured
- Try switching between Local and Spoonacular modes
- Check browser console for error messages

**"API connection failed"**
- Verify your API key is correct
- Check internet connection
- Ensure you haven't exceeded rate limits (150/day for free tier)

**"Meal plans not loading"**
- Check if you have a nutrition profile set up
- Try generating a new meal plan first
- Check browser console for errors

### Rate Limiting

The free Spoonacular tier allows 150 requests per day. The app includes:
- Automatic rate limiting
- Caching to reduce API calls
- Fallback to local database when limits are reached

### Debug Mode

To enable debug logging:

```bash
# Add to .env.local
DEBUG=True
LOGGING_LEVEL=DEBUG
```

Then check the console output for detailed information.

## 📱 Usage Tips

### Best Practices

1. **Set up your profile first** - This ensures better meal plan recommendations
2. **Use specific search terms** - "chicken pasta" works better than just "food"
3. **Try different cuisines** - Expand your culinary horizons
4. **Generate multiple plans** - Compare different AI-generated options

### Search Tips

- Use dietary filters for better results
- Try different meal types (breakfast, lunch, dinner, snack)
- Search for specific ingredients or cooking methods
- Use the "Load More" button to see additional recipes

## 🔄 Updates and Maintenance

### Updating Recipes

```bash
# Populate with fresh Spoonacular recipes
python manage.py populate_spoonacular_recipes --limit 50

# Remove old fallback recipes
python manage.py populate_spoonacular_recipes --remove-fallbacks
```

### Backup

```bash
# Backup your data before major updates
python manage.py dumpdata > backup.json
```

## 🆘 Support

If you encounter issues:

1. Check this guide first
2. Look at the browser console for error messages
3. Check the Django logs for backend issues
4. Verify your API key is working: `python setup_spoonacular.py`

## 🎉 What's Next?

- Enhanced nutrition tracking
- Recipe recommendations based on preferences
- Shopping list generation
- Integration with fitness trackers
- Social features for sharing meal plans

---

**Happy meal planning! 🍽️✨**