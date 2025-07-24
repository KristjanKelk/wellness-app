# AI-Powered Wellness Platform - Meal Planning & Nutrition

A comprehensive health and fitness tracking application with advanced AI-powered meal planning capabilities. Built with Django REST Framework, Vue.js, and integrated AI services for personalized nutrition planning.

## 🌟 Features

### Core Functionality
- **Advanced Authentication**: Email/password, OAuth (Google, GitHub), JWT tokens, 2FA support
- **Comprehensive Health Profiles**: Demographics, physical metrics, fitness assessments, dietary preferences
- **Health Analytics**: BMI calculations, wellness scoring, progress tracking with milestone detection
- **AI-Powered Insights**: Personalized recommendations using OpenAI integration
- **Data Visualization**: Interactive charts for weight tracking, progress monitoring, and activity analysis
- **Activity Tracking**: Log workouts, track different exercise types, monitor calories and distances
- **Goal Management**: Set and track fitness goals with progress indicators and achievement notifications

### Advanced Meal Planning Features
- **AI-Powered Meal Planning**: Sequential prompting with 3-step meal plan generation
- **Retrieval-Augmented Generation (RAG)**: Recipe database with vector embeddings for intelligent recipe suggestions
- **15+ Dietary Preferences**: Vegetarian, vegan, keto, paleo, Mediterranean, and more
- **10+ Allergy Support**: Comprehensive allergen tracking and avoidance
- **Smart Recipe Search**: Search by name, ingredients, cuisine with advanced filtering
- **Nutritional Analysis**: Complete macro/micronutrient tracking with visualizations
- **Shopping List Generation**: Categorized by 5+ food groups with quantity adjustments
- **Meal Customization**: Swap meals, regenerate plans, substitute ingredients
- **Function Calling**: Accurate nutritional calculations using AI function calling

## 🧠 AI Architecture & Strategy

### Prompt Engineering Strategy

Our meal planning system employs a sophisticated **3-step sequential prompting approach** that significantly improves the quality and personalization of generated meal plans compared to single-prompt methods:

#### Step 1: Strategic Analysis & Goal Setting
```
Input: User profile, dietary preferences, health goals, restrictions
Process: Analyze user requirements and create personalized nutrition strategy
Output: Detailed nutritional targets, meal distribution strategy, dietary approach
```

**Why this step matters**: This initial analysis ensures that all subsequent meal generation is aligned with user-specific health goals and constraints. By establishing clear parameters upfront, we avoid generating meals that don't fit the user's lifestyle or nutritional needs.

#### Step 2: Meal Structure & Framework Design
```
Input: Strategy from Step 1, available recipes database, seasonal preferences
Process: Design optimal meal timing, portion sizes, and macro distribution
Output: Structured meal framework with specific calorie and macro targets per meal
```

**Benefits**: This step creates a coherent meal plan structure before selecting specific recipes, ensuring balanced nutrition throughout the day and appropriate meal timing based on user preferences.

#### Step 3: Recipe Selection & Refinement
```
Input: Meal framework from Step 2, RAG-retrieved recipe candidates, user preferences
Process: Select specific recipes and ingredients, validate against restrictions
Output: Complete meal plan with recipes, ingredients, cooking instructions, and nutrition data
```

**RAG Integration**: This step leverages our recipe database through vector similarity search to find the most appropriate recipes that match both the nutritional requirements and user taste preferences.

### AI Model Selection Rationale

#### Primary Model: GPT-4 for Meal Planning
- **Choice Rationale**: GPT-4's superior reasoning capabilities and longer context window enable complex nutritional analysis and multi-step meal planning
- **Temperature Setting**: 0.7 for creative meal combinations while maintaining nutritional accuracy
- **Top-p Setting**: 0.9 to balance variety with relevance in recipe suggestions

#### Secondary Model: GPT-3.5-turbo for Function Calling
- **Use Case**: Nutritional calculations and dietary validation
- **Choice Rationale**: Faster response times for computational tasks while maintaining accuracy
- **Temperature Setting**: 0.3 for consistent, accurate calculations

#### Text-Embedding-Ada-002 for RAG
- **Purpose**: Generate 1536-dimensional embeddings for recipe and ingredient similarity search
- **Choice Rationale**: Optimized for semantic similarity in food and nutrition domain

### Few-Shot Learning Strategy

Our prompts include carefully selected few-shot examples to guide AI behavior:

#### Example Selection Criteria:
1. **Dietary Diversity**: Examples cover various dietary restrictions and preferences
2. **Complexity Range**: From simple snacks to complex multi-course meals
3. **Cultural Variety**: Examples from different cuisines to encourage diversity
4. **Nutritional Balance**: Demonstrate proper macro and micronutrient distribution

#### Sample Few-Shot Example:
```
User: Vegetarian, gluten-free, 1800 calories, high protein
Generated Plan:
- Breakfast: Quinoa porridge with almond butter and berries (450 kcal, 18g protein)
- Lunch: Lentil and vegetable curry with brown rice (520 kcal, 22g protein)
- Dinner: Grilled tempeh with roasted vegetables (480 kcal, 28g protein)
- Snacks: Greek yogurt with nuts (350 kcal, 20g protein)
```

## 🗄️ Data Model Decisions

### Recipe Data Structure
Our recipe model includes all required fields for comprehensive meal planning:

```python
class Recipe(models.Model):
    # Required Core Fields
    id = UUIDField()                    # Unique identifier
    title = CharField()                 # Recipe name
    cuisine = CharField()               # Cuisine type
    meal = CharField()                  # Meal type (breakfast/lunch/dinner/snack)
    servings = PositiveSmallIntegerField()  # Number of servings
    
    # Ingredients with detailed structure
    ingredients = JSONField()           # Array with id, name, quantity
    summary = TextField()               # Recipe description
    time = PositiveIntegerField()       # Total preparation time in minutes
    difficulty_level = CharField()      # easy/medium/hard
    dietary_tags = ArrayField()         # Dietary restriction tags
    source = CharField()                # Recipe source
    img = URLField()                    # Recipe image URL
    
    # Preparation instructions
    preparation = JSONField()           # Array with step, description, ingredients
    
    # Vector embeddings for RAG
    embedding_vector = ArrayField(FloatField(), size=1536)
```

**Design Rationale**: This structure balances comprehensive recipe information with efficient database operations. The JSON fields provide flexibility for complex ingredient lists and cooking instructions while maintaining queryability.

### Ingredient Data Structure
```python
class Ingredient(models.Model):
    # Required Core Fields
    id = UUIDField()                    # Unique identifier
    label = CharField()                 # Ingredient name
    unit = CharField()                  # Standard unit (grams/ml)
    quantity = FloatField()             # Base quantity
    
    # Nutritional information per 100g
    nutrition = JSONField()             # Object containing:
    # - calories: kcal per 100g
    # - carbs: grams per 100g
    # - protein: grams per 100g
    # - fats: grams per 100g
```

**Standardization Decision**: All measurements are standardized to metric units (grams for solids, milliliters for liquids, kilocalories for energy, minutes for time) to ensure consistency across the platform and simplify calculations.

### Nutritional Tracking Architecture
- **Daily Tracking**: Real-time calculation and storage of daily nutritional intake
- **Weekly/Monthly Trends**: Aggregated data for long-term analysis
- **Goal Comparison**: Automated deficit/surplus calculations with color-coded progress indicators
- **AI Analysis**: Regular summaries with improvement suggestions and achievement recognition

## 🚀 Retrieval-Augmented Generation (RAG) Implementation

### RAG Pipeline Architecture

Our RAG system enhances recipe generation quality through intelligent information retrieval:

```
1. Database → 2. Embedding → 3. Retrieval → 4. Augmentation → 5. Generation
```

#### 1. Database Component
- **Recipe Database**: 500+ verified recipes with comprehensive nutritional data
- **Ingredient Database**: 500+ ingredients with detailed nutritional profiles
- **Update Mechanism**: Community-driven feedback system for continuous improvement

#### 2. Embedding Component
- **Model**: OpenAI text-embedding-ada-002
- **Vector Dimensions**: 1536-dimensional embeddings
- **Indexing**: Automated embedding generation for new recipes and ingredients
- **Storage**: PostgreSQL with pgvector extension for efficient similarity search

#### 3. Retrieval Component
- **Similarity Search**: Cosine similarity for finding relevant recipes
- **Filtering**: Pre-filtering by dietary restrictions and allergens
- **Ranking**: Combined similarity score and user preference weighting
- **Diversity**: Ensures variety in retrieved recipes to prevent repetition

#### 4. Augmentation Component
- **Context Building**: Combines user preferences with retrieved recipe information
- **Prompt Enhancement**: Integrates RAG results into structured prompts
- **Nutritional Context**: Adds nutritional requirements to recipe context

#### 5. Generation Component
- **Model**: GPT-4 for complex meal planning decisions
- **Prompt Structure**: Multi-step prompts with RAG context integration
- **Validation**: Function calling to verify nutritional accuracy

### RAG Quality Improvements

**Compared to generation from scratch**, our RAG implementation provides:

1. **Accuracy**: Recipes based on verified nutritional data rather than AI hallucination
2. **Consistency**: Standardized ingredient measurements and cooking techniques
3. **Personalization**: Preference-based retrieval ensures relevant suggestions
4. **Scalability**: Easily expandable database without retraining models
5. **Community-Driven**: User feedback improves database quality over time

## ⚙️ Function Calling Implementation

### Nutritional Calculation Functions
All nutritional calculations are performed using AI function calling for accuracy and consistency:

```python
@function_call
def calculate_meal_nutrition(ingredients: List[Dict], servings: int) -> Dict:
    """
    Calculate precise nutritional values for a meal
    
    Args:
        ingredients: List of ingredients with quantities
        servings: Number of servings
    
    Returns:
        Nutritional breakdown per serving
    """
```

### Error Handling Coverage
Our function calling implementation includes comprehensive error handling:

- **Parsing Errors**: Malformed ingredient data validation
- **Missing Parameters**: Default value assignment and user notification
- **Invalid Values**: Range validation and correction suggestions
- **Execution Errors**: Graceful degradation to backup calculation methods
- **Timeout Errors**: Request timeout handling with retry logic
- **Rate Limits**: API rate limiting with exponential backoff
- **Connectivity Issues**: Offline mode with cached nutritional data

## 🛠 Technical Stack

### Backend
- **Framework**: Django 5.2 with Django REST Framework 3.16
- **Database**: PostgreSQL with pgvector extension for vector similarity
- **Authentication**: JWT with SimpleJWT, OAuth2 integration
- **AI Integration**: OpenAI GPT-4 and GPT-3.5-turbo for meal planning
- **Recipe API**: Spoonacular API integration with fallback to local database
- **Security**: 2FA with TOTP, email verification, rate limiting
- **Caching**: Redis for API response caching and rate limiting

### Frontend
- **Framework**: Vue.js 3 with Composition API
- **State Management**: Vuex 4 for centralized state
- **Routing**: Vue Router 4 with authentication guards
- **UI/UX**: Custom component library with SCSS styling
- **Charts**: Chart.js for nutritional data visualization
- **HTTP Client**: Axios with interceptors for token refresh

### AI & Data Processing
- **Vector Database**: PostgreSQL with pgvector extension
- **Embeddings**: OpenAI text-embedding-ada-002
- **Function Calling**: Structured AI function execution
- **Sequential Prompting**: Multi-step AI conversation management
- **RAG Pipeline**: Custom implementation with similarity search

## 📁 Project Architecture

```
wellness-platform/
├── backend/
│   ├── wellness_project/          # Django project settings
│   ├── users/                     # Authentication & user management
│   ├── health_profiles/           # Health data management
│   ├── analytics/                 # AI insights & wellness scoring
│   └── meal_planning/             # Meal planning & nutrition
│       ├── models.py             # Recipe, Ingredient, MealPlan models
│       ├── views.py              # Meal planning APIs
│       ├── services/             # Business logic
│       │   ├── ai_meal_planning_service.py
│       │   ├── rag_service.py
│       │   ├── spoonacular_service.py
│       │   └── nutrition_calculation_service.py
│       └── management/           # Database population commands
└── frontend/
    ├── src/
    │   ├── components/           # Reusable Vue components
    │   │   ├── meal-planning/    # Meal planning specific components
    │   │   ├── dashboard/        # Dashboard components
    │   │   └── ui/              # Base UI components
    │   ├── views/               # Page-level components
    │   ├── services/            # API service layers
    │   ├── store/               # Vuex state management
    │   └── assets/              # Styles, images & static files
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+ with pgvector extension
- OpenAI API key
- Spoonacular API key (optional, has fallback)

### Backend Setup

1. **Clone and setup virtual environment**
   ```bash
   git clone <repository-url>
   cd wellness-platform
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database setup**
   ```bash
   # Create PostgreSQL database with pgvector
   createdb wellness_db
   createuser -P wellness_user  # Password: wellness
   psql -d wellness_db -c "CREATE EXTENSION vector;"
   ```

4. **Environment configuration**
   ```bash
   # Create .env file with:
   SECRET_KEY=your-secret-key
   OPENAI_API_KEY=your-openai-api-key
   SPOONACULAR_API_KEY=your-spoonacular-api-key  # Optional
   GOOGLE_CLIENT_ID=your-google-oauth-client-id
   GOOGLE_CLIENT_SECRET=your-google-oauth-secret
   GITHUB_CLIENT_ID=your-github-oauth-client-id
   GITHUB_CLIENT_SECRET=your-github-oauth-secret
   ```

5. **Run migrations and populate database**
   ```bash
   python manage.py migrate
   python manage.py populate_nutrition_database  # Populates 500+ recipes/ingredients
   python manage.py createsuperuser
   python manage.py runserver
   ```

### Frontend Setup

1. **Install and run**
   ```bash
   cd frontend
   npm install
   npm run serve
   ```

2. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000/api/

## 📊 API Documentation

### Meal Planning Endpoints
```
# Recipe Management
GET/POST /api/meal-planning/recipes/           # Browse recipes (paginated)
POST /api/meal-planning/recipes/search/        # Advanced recipe search
GET /api/meal-planning/recipes/{id}/           # Recipe details
POST /api/meal-planning/recipes/{id}/rate/     # Rate recipe
POST /api/meal-planning/recipes/generate/      # AI recipe generation

# Meal Planning
GET/POST /api/meal-planning/meal-plans/        # Manage meal plans
POST /api/meal-planning/meal-plans/generate/   # Generate AI meal plan
POST /api/meal-planning/meal-plans/{id}/regenerate_meal/  # Regenerate specific meal
GET /api/meal-planning/meal-plans/{id}/alternatives/      # Get meal alternatives
POST /api/meal-planning/meal-plans/{id}/swap_meal/        # Swap meal
GET /api/meal-planning/meal-plans/{id}/analyze/           # Nutritional analysis

# Nutrition Tracking
GET/PUT /api/meal-planning/nutrition-profile/current/     # User nutrition profile
POST /api/meal-planning/nutrition-profile/calculate_targets/  # Auto-calculate targets
GET/POST /api/meal-planning/nutrition-logs/               # Daily nutrition tracking
GET /api/meal-planning/nutrition-logs/analytics/          # Nutrition analytics

# Shopping Lists
POST /api/meal-planning/meal-plans/{id}/shopping-list/    # Generate shopping list
PUT /api/meal-planning/shopping-lists/{id}/               # Update shopping list
```

## 🔒 Error Handling & Recovery

### API Error Handling
- **Rate Limiting**: Exponential backoff with user-friendly messages
- **Timeouts**: Graceful degradation to cached or default responses
- **Malformed Responses**: Input validation with detailed error messages
- **Connectivity Issues**: Offline mode with limited functionality

### Recovery Mechanisms
- **Caching**: Recipe and ingredient data cached for offline access
- **Retry Logic**: Automatic retry for transient failures
- **Alternative Models**: Fallback to GPT-3.5 if GPT-4 unavailable
- **Default Responses**: Sensible defaults when AI services are unavailable

### Content Versioning
- **Meal Plan History**: Previous versions accessible and restorable
- **Change Tracking**: Detailed audit log of meal plan modifications
- **Rollback Capability**: One-click restore to previous meal plan versions

## 🏗 Key Features Implementation

### Sequential Prompting Benefits
The 3-step sequential approach provides significant advantages:

1. **Better Context Understanding**: Each step builds upon previous outputs
2. **Improved Accuracy**: Iterative refinement catches inconsistencies
3. **Enhanced Personalization**: Progressive incorporation of user preferences
4. **Quality Assurance**: Multiple validation checkpoints throughout generation

### Wellness Score Integration
- **BMI Integration**: Weight goals used for calorie target calculation
- **Activity Level**: Adjusts portion sizes and macro distribution
- **Wellness Score Updates**: Nutrition compliance affects overall wellness metrics

### Nutritional Analysis Features
- **Real-time Tracking**: Live updates as meals are logged
- **Progress Visualization**: Color-coded progress bars and trend lines
- **AI Insights**: Weekly summaries with personalized recommendations
- **Goal Achievement**: Milestone tracking with celebration animations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper tests
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 🙏 Acknowledgments

- OpenAI for AI-powered meal planning capabilities
- Spoonacular for comprehensive recipe and ingredient database
- Chart.js for beautiful nutritional data visualizations
- Vue.js community for excellent documentation
- Django REST Framework for robust API development
