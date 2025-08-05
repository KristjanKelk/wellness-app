# AI Assistant for Wellness Platform

## Overview

The AI Assistant is a conversational interface that helps users interact with the wellness platform using natural language. It provides personalized health insights, nutrition information, and wellness guidance through an intuitive chat interface.

## Architecture

### Two-Layer Architecture

1. **Conversation Layer**
   - Handles direct user interactions and maintains conversation flow
   - Components:
     - Chat interface with message history
     - Input handling and validation
     - Response rendering and formatting
     - Session state tracking
     - Conversation history management
     - Context maintenance

2. **Data Access Layer**
   - Connects to platform features and processes data
   - Components:
     - Health data access functions
     - Nutrition data access functions
     - User profile integration
     - Function calling implementation
     - Data formatting for AI consumption
     - Error handling for data retrieval

## Features

### Core Capabilities

1. **Health Metrics Queries**
   - Current BMI, weight, and wellness score
   - Health goals and preferences
   - Progress tracking and activity history
   - Personalized health insights

2. **Nutrition Management**
   - Meal plan access and information
   - Recipe details and preparation steps
   - Nutritional analysis and recommendations
   - Dietary goals and restrictions

3. **Data Visualization**
   - Natural language chart generation
   - Weight trends, nutrition comparisons
   - Activity summaries and wellness scores
   - Interactive visualizations with Plotly

4. **Multi-turn Conversations**
   - Context-aware responses
   - Follow-up question handling
   - Reference resolution
   - Conversation memory management

## GenAI Techniques

### System Prompt Design

The system prompt defines the assistant's capabilities, personality, and constraints:

```python
system_prompt = f"""You are a wellness assistant helping {user_name} with health analytics and nutrition planning.

## Your capabilities include:
- Answering questions about health metrics (BMI, weight, wellness score, activity level)
- Providing information about meal plans and recipes
- Offering nutritional analysis and recommendations
- Providing general wellness guidance
- Describing trends from health data
- Comparing current metrics to targets and historical data

## Tone and personality:
- Friendly and encouraging
- Clear and straightforward
- Empathetic but not overly casual
- Use the user's name naturally in responses

## Response formatting:
- Use short, focused paragraphs
- Use bullet points for lists
- Use **bold** for key metrics and important information
- Present numerical data clearly with appropriate units (weight in kg, height in cm)
- For detailed mode: provide more context and explanations
- For concise mode: focus on key information only

## Important boundaries:
- You are NOT a medical professional and cannot provide medical advice
- For health concerns, suggest consulting with healthcare providers
- Stay within the scope of wellness guidance and data presentation
- Do not access or discuss other users' data
- Only provide information based on the user's own data
"""
```

### Function Calling

The assistant uses OpenAI's function calling to access user data:

1. **get_health_metrics** - Retrieves BMI, weight, wellness score
2. **get_meal_plan** - Accesses meal plans for specific timeframes
3. **get_nutrition_analysis** - Analyzes nutritional intake
4. **get_recipe_info** - Provides recipe details
5. **get_activity_summary** - Summarizes exercise data
6. **get_progress_report** - Generates progress towards goals

Example function definition:
```json
{
  "name": "get_health_metrics",
  "description": "Retrieves user's current health metrics",
  "parameters": {
    "type": "object",
    "properties": {
      "metric_type": {
        "type": "string",
        "enum": ["bmi", "weight", "wellness_score", "all"],
        "description": "The specific metric to retrieve"
      },
      "time_period": {
        "type": "string",
        "enum": ["current", "weekly", "monthly"],
        "description": "Time period for the metrics"
      }
    },
    "required": ["metric_type"]
  }
}
```

### Conversation Memory Management

- Maintains context across multiple conversation turns
- Automatic compression for long conversations
- Token optimization strategies
- Context windowing for efficient processing

### Response Formatting

- Structured templates for different query types
- Natural language descriptions of data
- Support for concise and detailed response modes
- Consistent formatting across all responses

## Setup Instructions

### Backend Setup

1. **Add AI Assistant to Django Settings**
```python
INSTALLED_APPS = [
    # ... other apps
    'ai_assistant',
]

# OpenAI Configuration
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
```

2. **Update URL Configuration**
```python
urlpatterns = [
    # ... other patterns
    path('api/ai-assistant/', include('ai_assistant.urls')),
]
```

3. **Install Dependencies**
```bash
pip install openai>=1.0.0 tiktoken>=0.5.0 plotly>=5.18.0
```

4. **Run Migrations**
```bash
python manage.py makemigrations ai_assistant
python manage.py migrate
```

5. **Set Environment Variable**
Add to your `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd frontend
npm install plotly.js-basic-dist
```

2. **Component Integration**
The AI Assistant component is automatically loaded in App.vue for authenticated users.

## Usage Guide

### Starting a Conversation

1. Click the floating chat button in the bottom-right corner
2. The assistant will greet you with example queries
3. Type your question or click an example

### Example Queries

**Health Metrics:**
- "What's my current BMI?"
- "How has my weight changed this month?"
- "What's my wellness score?"

**Progress Questions:**
- "How close am I to my weight goal?"
- "Am I making progress with my fitness level?"
- "How many active days did I have this week?"

**Meal Plans:**
- "What's on my meal plan today?"
- "What's for lunch tomorrow?"
- "Show me my meal plan for the week"

**Recipe Information:**
- "Tell me about my dinner recipe"
- "How do I prepare tonight's meal?"
- "What ingredients do I need for breakfast?"

**Nutritional Analysis:**
- "How many calories have I consumed today?"
- "Am I meeting my protein target?"
- "How's my nutrition this week?"

**General Wellness:**
- "How can I improve my sleep?"
- "What stretches help with lower back pain?"
- "What should I focus on to improve my wellness score?"

### Visualization Requests

The assistant can generate charts based on natural language:
- "Show me my weight trend for the last month"
- "Show me how my protein intake compares to the target"
- "Show me the breakdown of my macronutrients for today"

### Response Modes

Toggle between:
- **Concise Mode**: Brief, focused responses
- **Detailed Mode**: Comprehensive explanations

## Model Selection and Configuration

- **Model**: GPT-4O-mini for efficiency and cost-effectiveness
- **Temperature**: 0.7 for balanced creativity and accuracy
- **Top-p**: 0.9 for response diversity
- **Max Tokens**: 4096 for context window

## Token Management

- Efficient prompt design to minimize token usage
- Automatic conversation compression for long chats
- Context windowing to stay within limits
- Token counting for monitoring usage

## Error Handling

1. **Service Failures**: Graceful fallbacks with user-friendly messages
2. **Data Unavailability**: Clear explanations when data is missing
3. **Out-of-Scope Requests**: Polite redirects with alternatives
4. **Token Limits**: Automatic context compression

## Security and Privacy

1. **Data Access**: Users can only access their own data
2. **Medical Boundaries**: Clear disclaimers about medical advice
3. **Sensitive Information**: PII protection (no access to email, DOB, etc.)
4. **Authentication**: All endpoints require user authentication

## Extra Features Implemented

### Data Visualization
- Interactive chart generation through natural language
- Support for line charts, bar charts, and pie charts
- Proactive visualization suggestions based on context

### Context Summarization
- Automatic history compression for long conversations
- Dynamic context management based on relevance
- Maintains essential information while reducing tokens

## Testing Checklist

### Functional Requirements
- [ ] Health profile data access (BMI, weight, wellness score)
- [ ] Meal plan and recipe information retrieval
- [ ] Nutritional analysis and recommendations
- [ ] Multi-turn conversation support
- [ ] Context maintenance and follow-up questions
- [ ] Response formatting (concise/detailed modes)
- [ ] Visualization generation from natural language
- [ ] Error handling and boundary enforcement

### Security Testing
- [ ] Users cannot access other users' data
- [ ] PII protection (email, DOB, credentials)
- [ ] Medical advice boundaries enforced
- [ ] Authentication required for all endpoints

### Performance Testing
- [ ] Token usage optimization
- [ ] Conversation compression working
- [ ] Response times acceptable
- [ ] Chart generation performance

## Troubleshooting

### Common Issues

1. **"No OpenAI API Key"**
   - Ensure OPENAI_API_KEY is set in .env file
   - Restart the Django server after setting

2. **"Failed to generate chart"**
   - Check if user has sufficient data for visualization
   - Verify Plotly is properly installed in frontend

3. **"Context too long"**
   - Conversation will auto-compress
   - User can manually clear conversation

4. **"No health/nutrition profile"**
   - User needs to complete profile setup first
   - Assistant will indicate missing data

## Future Enhancements

1. **Voice Integration**: Speech-to-text and text-to-speech
2. **Proactive Insights**: Daily/weekly health summaries
3. **Goal Setting**: Interactive goal creation through chat
4. **Export Features**: Chat history and insights export
5. **Multi-language Support**: Internationalization