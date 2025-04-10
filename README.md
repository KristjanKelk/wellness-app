# Wellness Platform

A modern AI-powered wellness application that helps users track their health metrics, receive personalized recommendations, and visualize their progress.

## Features

- **User Health Profiles**: Collect and manage health data including demographics, physical metrics, lifestyle indicators, and fitness goals
- **Authentication System**: Secure login with email/password, JWT tokens, and OAuth providers
- **Health Metrics Tracking**: Track weight history, BMI, activity levels, and more
- **Wellness Score**: Comprehensive scoring system calculated from various health factors
- **AI-Powered Insights**: Personalized health recommendations based on user data
- **Data Visualization**: Interactive charts and visualizations to track progress
- **Responsive Design**: Works on desktop and mobile devices

## Technical Stack

### Backend
- **Django**: Web framework
- **Django REST Framework**: API development
- **PostgreSQL**: Database
- **JWT**: Authentication with access/refresh tokens
- **OAuth**: Multiple authentication options

### Frontend
- **Vue.js 3**: JS framework
- **Vuex**: State management
- **Vue Router**: Navigation
- **Chart.js**: Data visualization
- **Axios**: API communication

## Project Structure

```
wellness-platform/
├── wellness_project/       # Django project settings
├── users/                  # User authentication and profiles
├── health_profiles/        # Health data models and APIs
├── analytics/              # Wellness scores and AI insights
└── frontend/               # Vue.js frontend application
    ├── src/
    │   ├── components/     # Reusable Vue components
    │   ├── views/          # Page components
    │   ├── services/       # API services
    │   ├── store/          # Vuex state management
    │   └── router/         # Vue Router configuration
    └── public/             # Static assets
```

## Setup Instructions

### Backend Setup

1. Clone the repository
   ```
   git clone <repository-url>
   cd wellness-platform
   ```

2. Set up a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Set up PostgreSQL
   ```
   # Create a PostgreSQL database named 'wellness_db'
   # Create a user 'wellness_user' with password 'wellness'
   # Grant all privileges on wellness_db to wellness_user
   ```

5. Apply migrations
   ```
   python manage.py migrate
   ```

6. Create a superuser
   ```
   python manage.py createsuperuser
   ```

7. Run the development server
   ```
   python manage.py runserver
   ```

### Frontend Setup

1. Navigate to the frontend directory
   ```
   cd frontend
   ```

2. Install dependencies
   ```
   npm install
   ```

3. Run the development server
   ```
   npm run serve
   ```

4. Access the application at http://localhost:8080

## API Endpoints

### Authentication
- `POST /api/register/`: Register a new user
- `POST /api/token/`: Obtain JWT token pair
- `POST /api/token/refresh/`: Refresh access token
- `POST /api/token/verify/`: Verify token validity

### Health Profiles
- `GET /api/health-profiles/my_profile/`: Get current user's profile
- `PUT /api/health-profiles/my_profile/`: Update profile
- `GET /api/weight-history/`: Get weight history
- `POST /api/weight-history/`: Add new weight entry

### Analytics
- `GET /api/insights/`: Get AI insights
- `POST /api/insights/generate/`: Generate new insights
- `GET /api/wellness-scores/`: Get wellness scores
- `POST /api/wellness-scores/calculate/`: Calculate new wellness score

## Security Considerations

- JWT tokens expire after 15 minutes
- Refresh tokens valid for 14 days
- All sensitive user data is encrypted
- Email verification required after registration
- API endpoints protected by authentication
- Input validation for all form submissions

## Future Enhancements

- Integration with fitness trackers and wearable devices
- Nutrition planning and meal tracking
- Advanced AI-powered workout recommendations
- Social features for community support
- Mobile applications for iOS and Android

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request