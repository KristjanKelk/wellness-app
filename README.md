# AI-Powered Wellness Platform

A comprehensive health and fitness tracking application that leverages artificial intelligence to provide personalized wellness insights and recommendations. Built with Django REST Framework and Vue.js.

## 🌐 Live Demo

**Experience the platform live on Render:**
- **Frontend Application**: [https://wellness-app-fronend.onrender.com](https://wellness-app-fronend.onrender.com)
- **Backend API**: [https://wellness-app-tx2c.onrender.com](https://wellness-app-tx2c.onrender.com)
- **API Health Check**: [https://wellness-app-tx2c.onrender.com/api/health/](https://wellness-app-tx2c.onrender.com/api/health/)

*Note: The application is hosted on Render's free tier, which may experience brief startup delays (15-30 seconds) if the service has been inactive.*

##  Features

### Core Functionality
- ** Advanced Authentication**: Email/password, OAuth (Google, GitHub), JWT tokens, 2FA support
- ** Comprehensive Health Profiles**: Demographics, physical metrics, fitness assessments, dietary preferences
- ** Health Analytics**: BMI calculations, wellness scoring, progress tracking with milestone detection
- ** AI-Powered Insights**: Personalized recommendations using OpenAI integration
- ** Data Visualization**: Interactive charts for weight tracking, progress monitoring, and activity analysis
- ** Activity Tracking**: Log workouts, track different exercise types, monitor calories and distances
- ** Goal Management**: Set and track fitness goals with progress indicators and achievement notifications
- ** AI Assistant**: Conversational interface for natural language health queries and personalized guidance

### Meal Planning & Nutrition
- ** Recipe Database**: Browse thousands of recipes with detailed nutritional information
- ** Smart Recipe Search**: Advanced filtering by dietary restrictions, cuisine type, and nutritional content
- ** AI Meal Planning**: Generate personalized weekly meal plans based on dietary preferences and health goals
- ** Recipe Rating System**: Rate and save favorite recipes for future meal planning
- ** Shopping List Generation**: Automatically create shopping lists from selected meal plans
- ** Spoonacular Integration**: Powered by comprehensive recipe and nutrition database

### Advanced Features
- ** Email Verification**: Secure account activation and password recovery
- ** Data Privacy**: GDPR-compliant data handling with encryption at rest and in transit
- ** Responsive Design**: Mobile-first approach with cross-device compatibility
- ** Real-time Updates**: Live progress tracking and instant feedback
- ** Data Export**: Export all personal health data in JSON format
- ** Milestone Tracking**: Automatic achievement detection and celebration
- ** Service Hibernation Handling**: Intelligent backend wakeup for seamless user experience
- ** Natural Language Processing**: AI-powered chat interface with context-aware responses
- ** Smart Visualizations**: Generate charts from natural language requests
- ** Conversation Memory**: Multi-turn conversations with context retention

## 🛠 Technical Stack

### Backend
- **Framework**: Django 5.2 with Django REST Framework 3.16
- **Database**: PostgreSQL with optimized queries
- **Authentication**: JWT with SimpleJWT, OAuth2 integration
- **AI Integration**: OpenAI GPT-3.5-turbo for conversational assistant and health insights
- **Recipe API**: Spoonacular API for meal planning and nutrition data
- **Security**: 2FA with TOTP, email verification, rate limiting
- **NLP**: OpenAI function calling for structured data access
- **API Documentation**: RESTful APIs with proper serialization
- **Deployment**: Render.com with environment-based configuration

### Frontend
- **Framework**: Vue.js 3 with Composition API
- **State Management**: Vuex 4 for centralized state
- **Routing**: Vue Router 4 with authentication guards
- **UI/UX**: Custom component library with SCSS styling
- **Charts**: Chart.js for data visualization
- **HTTP Client**: Axios with interceptors for token refresh
- **Service Management**: Intelligent backend hibernation handling

### Development Tools
- **Code Quality**: ESLint for JavaScript, proper Python formatting
- **Build Tools**: Vue CLI with hot reloading
- **Version Control**: Git with feature branch workflow
- **Deployment**: Automated deployment pipeline with Render.com

## 📁 Project Architecture

```
wellness-platform/
├── backend/
│   ├── wellness_project/          # Django project settings
│   ├── users/                     # Authentication & user management
│   │   ├── models.py             # Custom user model with 2FA
│   │   ├── views.py              # Auth views & OAuth integration
│   │   ├── serializers.py        # User data serialization
│   │   └── oauth.py              # OAuth provider implementations
│   ├── health_profiles/           # Health data management
│   │   ├── models.py             # Health profile & weight history
│   │   ├── views.py              # Profile & activity tracking APIs
│   │   └── serializers.py        # Health data serialization
│   ├── analytics/                 # AI insights & wellness scoring
│   │   ├── models.py             # Wellness scores & milestones
│   │   ├── views.py              # AI integration & analytics
│   │   ├── services.py           # Business logic & calculations
│   │   └── serializers.py        # Analytics data serialization
│   └── assistant/                # Conversation + DAL for unified assistant
│       ├── models.py             # Conversation sessions/messages
│       ├── views.py              # Conversation endpoint + validation
│       ├── services.py           # Data Access Layer
│       └── serializers.py        # DTOs for requests/responses
└── frontend/
    ├── src/
    │   ├── components/           # Reusable Vue components
    │   │   ├── dashboard/        # Dashboard-specific components
    │   │   ├── auth/            # Authentication components
    │   │   └── ui/              # Base UI components
    │   ├── views/               # Page-level components
    │   ├── services/            # API service layers
    │   ├── store/               # Vuex state management
    │   ├── router/              # Navigation & route guards
    │   └── assets/              # Styles, images & static files
    └── public/                  # Static assets
```

## 🚀 Getting Started

### Quick Demo
Visit the live application at [wellness-app-fronend.onrender.com](https://wellness-app-fronend.onrender.com) to explore all features without local setup.

*First load may take 15-30 seconds as the service wakes from hibernation.*

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- OpenAI API key (for AI features)
- Spoonacular API key (for meal planning features)

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
   # Create PostgreSQL database
   createdb wellness_db
   createuser -P wellness_user  # Password: wellness
   ```

4. **Environment configuration**
   ```bash
   # Create .env file with:
   SECRET_KEY=your-secret-key
   OPENAI_API_KEY=your-openai-api-key
   SPOONACULAR_API_KEY=your-spoonacular-api-key
   GOOGLE_CLIENT_ID=your-google-oauth-client-id
   GOOGLE_CLIENT_SECRET=your-google-oauth-secret
   GITHUB_CLIENT_ID=your-github-oauth-client-id
   GITHUB_CLIENT_SECRET=your-github-oauth-secret
   ```

5. **Run migrations and start server**
   ```bash
   python manage.py migrate
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

## 🌍 Deployment & Production

### Live Environment
The application is deployed on Render.com with the following configuration:

- **Backend Service**: `wellness-app-tx2c.onrender.com`
- **Frontend Service**: `wellness-app-fronend.onrender.com`
- **Environment**: Production-ready with all security features enabled
- **Database**: PostgreSQL with SSL encryption
- **CORS**: Configured for secure cross-origin requests

### Service Management
- **Auto-wake**: The frontend automatically wakes hibernating backend services
- **Health Monitoring**: Built-in health checks and service status indicators
- **Error Handling**: Graceful handling of service timeouts and connectivity issues

## 📊 API Documentation

### Authentication Endpoints
```
POST /api/register/                    # User registration
POST /api/token/                       # Login (JWT token)
POST /api/token/refresh/               # Refresh access token
POST /api/users/verify-email/          # Email verification
POST /api/users/2fa/generate/          # Generate 2FA QR code
POST /api/oauth/google/                # Google OAuth
POST /api/oauth/github/                # GitHub OAuth
```

### Health Profile Endpoints
```
GET/PUT /api/health-profiles/my_profile/  # User health profile
GET/POST /api/weight-history/             # Weight tracking
GET /api/weight-history/weekly_averages/  # Weekly weight data
GET/POST /api/activities/                 # Activity logging
GET /api/activities/summary/              # Activity statistics
```

### Analytics Endpoints
```
GET/POST /api/insights/                   # AI health insights
POST /api/insights/generate/              # Generate new insights
GET/POST /api/wellness-scores/            # Wellness scoring
POST /api/wellness-scores/calculate/      # Calculate new score
GET /api/analytics/milestones/            # Achievement tracking
```

### Meal Planning & Recipe Endpoints
```
GET/POST /api/recipes/                    # Browse recipes (paginated)
POST /api/recipes/search/                 # Advanced recipe search
POST /api/recipes/{id}/rate/              # Rate a recipe
GET/POST /api/meal-plans/                 # Manage meal plans
GET /api/meal-plans/today/                # Convenience: today’s plan (assistant)
POST /api/meal-plans/generate/            # Generate meal plan with AI
GET /api/shopping-lists/                  # Generate shopping lists
POST /api/recipes/favorites/              # Manage favorite recipes
```
Recipe list and search endpoints support pagination. Clients may specify
`page_size` to control results per page (default is 20).

### Assistant Endpoints
```
POST /api/assistant/message/              # Unified assistant conversation endpoint
```
- **Request**:
  ```json
  { "session_id": 123, "message": "What's my meal plan for the week?", "mode": "concise" }
  ```
- **Response**:
  ```json
  { "session_id": 123, "reply": "...", "mode": "concise", "context": {} }
  ```

## 🧠 System Prompt Engineering Strategy
- Centralized in settings as `ASSISTANT_SYSTEM_PROMPT` and `ASSISTANT_RESPONSE_FORMATS`.
- Guides consistent output structure with examples for metrics, progress, meal plans, recipes, and nutrition analysis.
- Enforces safety boundaries: no sensitive PII beyond name; medical cautioning.

## 🤖 AI Model Selection Rationale
- Uses OpenAI Chat (configured in analytics and meal planning services) with:
  - GPT-3.5/4-turbo for generation/analysis depending on task.
  - Lower temperature for nutrition analysis, moderate for creative meal planning.
- Concise/detailed modes supported at the conversation layer instead of randomizing with high temperature.

## 💬 Conversation Management Approach
- `assistant` app stores `ConversationSession` and `ConversationMessage` for multi-turn context.
- Unified endpoint `/api/assistant/message/` routes intents to the Data Access Layer.
- Maintains context across re-opens via persisted session history.

## 🛡️ Error Handling Methods
- Parameter validation with clear messages (e.g., period, days ranges).
- Structured not-found errors when data is unavailable for a date or period.
- Graceful fallbacks for AI outages (see analytics summary and AI insights).

## 🧩 Function Calling Implementation Details
- OpenAI function schemas defined in settings and used in `meal_planning/services/ai_nutrition_profile_service.py`.
- Parameter validation enforced server-side before execution.

## 🔍 Data Access Layer
- `assistant/services.py` unifies health metrics, progress, meal plan retrieval, recipes, and nutrition analysis.
- Ensures metric units are metric (kg, cm).
- Prevents access to other users’ data; always scoped to authenticated user.

## 🔐 Privacy & Security
- Assistant blocks requests for emails, DOB, credentials; only uses user’s name.
- Meal plans and analytics require JWT authentication.

## 📈 Examples and Usage
- **Health metrics**: “How are my weight and BMI doing?” → unified reply with both metrics and interpretation.
- **Progress**: “How has my weight changed this month?” → trend with start/end/change and pattern.
- **Meal plans**: “What’s my meal plan for today?” → list of meals with types and kcal.
- **Recipe info**: “How do I prepare tonight’s dinner?” → ingredients and step-by-step instructions.
- **Nutritional analysis**: “Have I been getting enough protein this week?” → average vs target and next steps.
- **General wellness**: Handles follow-ups with session context.

## 🔒 Safety and Limitations for Medical Advice
- The assistant avoids diagnosis and recommends professional consultation for symptoms like chest pain during exercise.

## 🏗 Key Features Implementation

### Wellness Score Calculation
The platform calculates a comprehensive wellness score (0-100) based on:
- **BMI Score** (30%): Optimal range scoring with penalties for extremes
- **Activity Score** (30%): Based on logged activities and frequency
- **Progress Score** (20%): Goal achievement and milestone tracking
- **Habits Score** (20%): Consistency and healthy behavior patterns

### AI Integration
- **Personalized Insights**: Uses OpenAI GPT-3.5-turbo to analyze user data
- **Context-Aware Recommendations**: Considers user goals, restrictions, and history
- **Adaptive Learning**: Improves recommendations based on user feedback
- **Privacy-First**: PII is stripped before AI processing

### Milestone System
Automatic tracking and celebration of achievements:
- **Weight Goals**: 5% increments toward target weight
- **Activity Milestones**: Increased weekly activity days
- **Streak Achievements**: Consistent logging and exercise habits
- **Special Celebrations**: Goal completion with confetti animations

## 🔒 Security & Privacy

- **Data Encryption**: All sensitive data encrypted at rest and in transit
- **JWT Security**: Short-lived access tokens (30 min) with secure refresh
- **Rate Limiting**: API abuse prevention with user-specific limits
- **Input Validation**: Comprehensive server-side validation
- **CORS Configuration**: Secure cross-origin request handling
- **2FA Support**: TOTP-based two-factor authentication
- **Data Export**: GDPR-compliant data portability

---

**🔗 Quick Links:**
- [Live Application](https://wellness-app-fronend.onrender.com)
- [API Documentation](https://wellness-app-tx2c.onrender.com/api/)
- [Health Check](https://wellness-app-tx2c.onrender.com/api/health/)

*Built with ❤️ for better health and wellness*

## 🧪 Assistant: Setup & Usage
- Ensure you are authenticated (JWT) when calling the assistant API.
- Send messages to `/api/assistant/message/` with optional `session_id` to maintain multi-turn context.
- Modes:
  - `concise` (default) for brief answers
  - `detailed` for more context and explanation
- Example curl:
  ```bash
  curl -X POST http://localhost:8000/api/assistant/message/ \
    -H "Authorization: Bearer <ACCESS_TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"message":"What\'s my meal plan for today?","mode":"concise"}'
  ```
