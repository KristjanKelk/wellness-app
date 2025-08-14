# ai_assistant/views.py
import json
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from .models import Conversation, Message, UserPreference
from .serializers import ConversationSerializer, MessageSerializer, UserPreferenceSerializer
from .conversation_manager import ConversationManager
from .visualization_service import VisualizationService


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing conversations"""
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user, is_active=True)
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send a message to the AI assistant"""
        message = request.data.get('message', '').strip()
        conversation_id = request.data.get('conversation_id')
        
        if not message:
            return Response(
                {"error": "Message cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create conversation manager
            manager = ConversationManager(request.user, conversation_id)
            
            # Send message
            result = manager.send_message(message)
            
            # Check for visualization suggestions
            viz_service = VisualizationService(request.user)
            suggestions = viz_service.suggest_visualization(message)
            if suggestions:
                result['visualization_suggestions'] = suggestions
            
            # Ensure consistent success shape
            if 'success' not in result:
                result['success'] = True
            return Response(result)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in send_message: {str(e)}", exc_info=True)
            
            return Response(
                {"success": False, "message": "Sorry, something went wrong while processing your message. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get conversation history"""
        try:
            conversation = self.get_object()
            limit = int(request.query_params.get('limit', 50))
            
            messages = Message.objects.filter(
                conversation=conversation,
                role__in=['user', 'assistant']
            ).order_by('-created_at')[:limit]
            
            serializer = MessageSerializer(messages, many=True)
            return Response({
                "conversation_id": str(conversation.id),
                "messages": reversed(serializer.data)
            })
            
        except Exception as e:
            return Response(
                {"success": False, "message": "Sorry, we couldn't load your conversation history. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get the active conversation or create new one"""
        conversation = Conversation.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-updated_at').first()
        
        if not conversation:
            conversation = Conversation.objects.create(user=request.user)
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Clear a conversation"""
        conversation = self.get_object()
        conversation.is_active = False
        conversation.save()
        
        # Create new conversation
        new_conversation = Conversation.objects.create(user=request.user)
        serializer = self.get_serializer(new_conversation)
        
        return Response({
            "message": "Conversation cleared",
            "new_conversation": serializer.data
        })


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing messages"""
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        return Message.objects.filter(
            conversation__user=self.request.user
        ).select_related('conversation')


class UserPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user preferences"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserPreferenceSerializer
    
    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'post'])
    def current(self, request):
        """Get or update current user preferences"""
        preferences, created = UserPreference.objects.get_or_create(
            user=request.user
        )
        
        if request.method == 'POST':
            serializer = self.get_serializer(preferences, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)


class VisualizationViewSet(viewsets.ViewSet):
    """ViewSet for generating visualizations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a visualization based on natural language request"""
        chart_request = (request.data.get('request') or '').strip()
        time_period = request.data.get('time_period', 'month')
        
        # Support direct chart_type to improve reliability from frontend
        chart_type = (request.data.get('chart_type') or '').strip()
        if chart_type and not chart_request:
            chart_request = chart_type
        
        if not chart_request:
            return Response(
                {"error": "Chart request cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            viz_service = VisualizationService(request.user)
            chart_data = viz_service.generate_chart(chart_request, time_period)
            
            if 'error' in chart_data:
                message = chart_data.get('error')
                # Return 200 for no-data cases so frontend can show a friendly notice instead of an error toast
                if isinstance(message, str) and message.lower().startswith('no '):
                    return Response({"success": False, "message": message}, status=status.HTTP_200_OK)
                return Response({"success": False, "message": message}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(chart_data)
            
        except Exception as e:
            return Response(
                {"success": False, "message": "Sorry, we couldn't generate that chart right now. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def available_charts(self, request):
        """Get list of available chart types"""
        return Response({
            "charts": [
                {
                    "type": "weight_trend",
                    "name": "Weight Trend",
                    "description": "Track weight changes over time",
                    "example": "Show me my weight trend for the last month"
                },
                {
                    "type": "protein_comparison",
                    "name": "Protein Intake vs Target",
                    "description": "Compare actual protein intake with daily targets",
                    "example": "Show me how my protein intake compares to the target"
                },
                {
                    "type": "macronutrient_breakdown",
                    "name": "Macronutrient Breakdown",
                    "description": "View proportions of protein, carbs, and fats",
                    "example": "Show me the breakdown of my macronutrients for today"
                },
                {
                    "type": "calorie_trend",
                    "name": "Calorie Intake Trend",
                    "description": "Track daily calorie consumption",
                    "example": "Show me my calorie intake trend this week"
                },
                {
                    "type": "activity_summary",
                    "name": "Activity Summary",
                    "description": "Summarize exercise and activities",
                    "example": "Show me my activity summary for the week"
                },
                {
                    "type": "wellness_score",
                    "name": "Wellness Score Trend",
                    "description": "Track overall wellness score over time",
                    "example": "Show me my wellness score trend"
                }
            ]
        })


class ChatExampleViewSet(viewsets.ViewSet):
    """ViewSet for providing chat examples"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def examples(self, request):
        """Get example questions for different categories"""
        return Response({
            "categories": [
                {
                    "name": "Health Metrics",
                    "examples": [
                        "What's my current BMI?",
                        "How has my weight changed this month?",
                        "What's my wellness score?"
                    ]
                },
                {
                    "name": "Progress Questions",
                    "examples": [
                        "How close am I to my weight goal?",
                        "Am I making progress with my fitness level?",
                        "How many active days did I have this week?"
                    ]
                },
                {
                    "name": "Meal Plans",
                    "examples": [
                        "What's on my meal plan today?",
                        "What's for lunch tomorrow?",
                        "Show me my meal plan for the week"
                    ]
                },
                {
                    "name": "Recipe Information",
                    "examples": [
                        "Tell me about my dinner recipe",
                        "How do I prepare tonight's meal?",
                        "What ingredients do I need for breakfast?"
                    ]
                },
                {
                    "name": "Nutritional Analysis",
                    "examples": [
                        "How many calories have I consumed today?",
                        "Am I meeting my protein target?",
                        "How's my nutrition this week?"
                    ]
                },
                {
                    "name": "General Wellness",
                    "examples": [
                        "How can I improve my sleep?",
                        "What stretches help with lower back pain?",
                        "What should I focus on to improve my wellness score?"
                    ]
                }
            ]
        })