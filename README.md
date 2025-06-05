# AI-Powered Wellness Platform

A comprehensive health and fitness tracking application that leverages artificial intelligence to provide personalized wellness insights and recommendations. Built with Django REST Framework and Vue.js.

##  Features

### Core Functionality
- ** Advanced Authentication**: Email/password, OAuth (Google, GitHub), JWT tokens, 2FA support
- ** Comprehensive Health Profiles**: Demographics, physical metrics, fitness assessments, dietary preferences
- ** Health Analytics**: BMI calculations, wellness scoring, progress tracking with milestone detection
- ** AI-Powered Insights**: Personalized recommendations using OpenAI integration
- ** Data Visualization**: Interactive charts for weight tracking, progress monitoring, and activity analysis
- ** Activity Tracking**: Log workouts, track different exercise types, monitor calories and distances
- ** Goal Management**: Set and track fitness goals with progress indicators and achievement notifications

### Advanced Features
- ** Email Verification**: Secure account activation and password recovery
- ** Data Privacy**: GDPR-compliant data handling with encryption at rest and in transit
- ** Responsive Design**: Mobile-first approach with cross-device compatibility
- ** Real-time Updates**: Live progress tracking and instant feedback
- ** Data Export**: Export all personal health data in JSON format
- ** Milestone Tracking**: Automatic achievement detection and celebration

## 🛠 Technical Stack

### Backend
- **Framework**: Django 5.2 with Django REST Framework 3.16
- **Database**: PostgreSQL with optimized queries
- **Authentication**: JWT with SimpleJWT, OAuth2 integration
- **AI Integration**: OpenAI GPT-3.5-turbo for health insights
- **Security**: 2FA with TOTP, email verification, rate limiting
- **API Documentation**: RESTful APIs with proper serialization

### Frontend
- **Framework**: Vue.js 3 with Composition API
- **State Management**: Vuex 4 for centralized state
- **Routing**: Vue Router 4 with authentication guards
- **UI/UX**: Custom component library with SCSS styling
- **Charts**: Chart.js for data visualization
- **HTTP Client**: Axios with interceptors for token refresh

### Development Tools
- **Code Quality**: ESLint for JavaScript, proper Python formatting
- **Build Tools**: Vue CLI with hot reloading
- **Version Control**: Git with feature branch workflow

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
│   └── analytics/                 # AI insights & wellness scoring
│       ├── models.py             # Wellness scores & milestones
│       ├── views.py              # AI integration & analytics
│       ├── services.py           # Business logic & calculations
│       └── serializers.py        # Analytics data serialization
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

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- OpenAI API key (for AI features)

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper tests
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request


## 🙏 Acknowledgments

- OpenAI for AI-powered health insights
- Chart.js for beautiful data visualizations
- Vue.js community for excellent documentation
- Django REST Framework for robust API development
