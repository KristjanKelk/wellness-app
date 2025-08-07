from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime

from .models import ConversationSession, ConversationMessage
from .serializers import (
    ConversationSessionSerializer,
    ConversationMessageSerializer,
    AssistantMessageRequestSerializer,
    AssistantMessageResponseSerializer,
)
from .services import AssistantDAL, DataNotFound, ValidationFailure


SAFE_PII_WHITELIST = {'name'}


def sanitize_pii_in_text(text: str) -> str:
    # Do not solicit or echo emails, DOB, credentials; keep simple guardrails
    banned_keywords = ['email', 'dob', 'date of birth', 'password', 'credential', 'token', 'api key']
    lowered = text.lower()
    if any(k in lowered for k in banned_keywords):
        return "I can\'t request or display sensitive personal data like emails, dates of birth, or credentials."
    return text


class AssistantViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def message(self, request):
        serializer = AssistantMessageRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Invalid input', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        session = None
        if serializer.validated_data.get('session_id'):
            try:
                session = ConversationSession.objects.get(id=serializer.validated_data['session_id'], user=request.user)
            except ConversationSession.DoesNotExist:
                return Response({'error': 'Invalid session_id'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            session = ConversationSession.objects.create(user=request.user, mode=serializer.validated_data.get('mode') or 'concise')

        # Update mode if provided
        if serializer.validated_data.get('mode'):
            session.mode = serializer.validated_data['mode']
            session.save(update_fields=['mode', 'updated_at'])

        raw_message = serializer.validated_data['message']
        if raw_message is None or not str(raw_message).strip():
            return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
        if len(raw_message) > 5000:
            return Response({'error': 'Message too long'}, status=status.HTTP_413_PAYLOAD_TOO_LARGE)

        # Persist user message
        ConversationMessage.objects.create(session=session, role='user', content=raw_message)

        # Safety: deny sensitive PII and cross-user data/jailbreak attempts
        lowered = raw_message.lower()
        jail_keywords = ['other users', 'all users', 'admin mode', 'pretend i\'m user', 'another user', 'show me all users', 'user id']
        pii_keywords = ['email', 'dob', 'date of birth', 'password', 'credential', 'token', 'api key']
        if any(k in lowered for k in jail_keywords) or any(k in lowered for k in pii_keywords):
            reply_text = "I can\'t access other users or handle sensitive personal data (emails, DOB, credentials). I can help with your metrics, meal plans, and nutrition instead."
            ConversationMessage.objects.create(session=session, role='assistant', content=reply_text)
            return Response({'session_id': session.id, 'reply': reply_text, 'mode': session.mode, 'context': session.context_state}, status=status.HTTP_403_FORBIDDEN)

        # Retrieve previous assistant payload for contextual follow-ups
        last_assistant = session.messages.filter(role='assistant').order_by('-created_at').first()
        last_payload = (last_assistant.metadata or {}).get('payload') if last_assistant and last_assistant.metadata else None

        # Simple intent detection (rule-based for now)
        text = raw_message.lower()
        dal = AssistantDAL()
        reply_payload = {}
        try:
            # Follow-up: "Is that enough protein?"
            if ('enough protein' in text or ('enough' in text and 'protein' in text)) and last_payload and last_payload.get('type') == 'protein_analysis':
                d = last_payload.get('data', {})
                reply_payload = {'type': 'protein_analysis', 'data': d}
            elif 'meal plan' in text and 'week' in text:
                data = dal.get_meal_plan_for_week(request.user)
                reply_payload = {
                    'type': 'meal_plan_week',
                    'data': data,
                }
            elif 'meal plan' in text or ('meal' in text and 'today' in text):
                data = dal.get_meal_plan_for_date(request.user)
                reply_payload = {
                    'type': 'meal_plan_today',
                    'data': data,
                }
            elif 'prepare' in text and 'dinner' in text:
                data = dal.get_tonight_dinner_recipe(request.user)
                reply_payload = {
                    'type': 'recipe_prep',
                    'data': data,
                }
            elif 'protein' in text and ('week' in text or 'this week' in text):
                data = dal.analyze_protein_intake_vs_target(request.user, days=7)
                reply_payload = {
                    'type': 'protein_analysis',
                    'data': data,
                }
            elif 'wellness score' in text and ('improve' in text or 'focus' in text):
                data = dal.recommend_wellness_focus(request.user)
                reply_payload = {
                    'type': 'wellness_focus',
                    'data': data,
                }
            elif 'trend' in text and 'weight' in text:
                data = dal.summarize_weight_trend(request.user, days=30)
                reply_payload = {
                    'type': 'weight_trend',
                    'data': data,
                }
            elif 'goal' in text:
                data = dal.get_health_overview(request.user)
                reply_payload = {
                    'type': 'goals',
                    'data': {'goal': data.get('goal')}
                }
            elif ('bmi' in text) or ('weight' in text) or ('wellness score' in text) or ('activity' in text):
                data = dal.get_health_overview(request.user)
                reply_payload = {
                    'type': 'metrics_overview',
                    'data': data,
                }
            else:
                # Fallback to overview as a helpful default
                data = dal.get_health_overview(request.user)
                reply_payload = {
                    'type': 'metrics_overview',
                    'data': data,
                }
        except ValidationFailure as ve:
            reply_text = f"Input error: {str(ve)}"
            ConversationMessage.objects.create(session=session, role='assistant', content=reply_text)
            return Response({'session_id': session.id, 'reply': reply_text, 'mode': session.mode, 'context': session.context_state}, status=status.HTTP_400_BAD_REQUEST)
        except DataNotFound as dne:
            reply_text = f"{str(dne)}"
            ConversationMessage.objects.create(session=session, role='assistant', content=reply_text)
            return Response({'session_id': session.id, 'reply': reply_text, 'mode': session.mode, 'context': session.context_state}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            reply_text = "Sorry, something went wrong while processing your request."
            ConversationMessage.objects.create(session=session, role='assistant', content=reply_text, metadata={'error': str(e)})
            return Response({'session_id': session.id, 'reply': reply_text, 'mode': session.mode, 'context': session.context_state}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Build natural language reply with modes, avoid sensitive PII
        reply_text = build_reply_text(reply_payload, mode=session.mode)
        reply_text = sanitize_pii_in_text(reply_text)

        # Persist assistant reply
        ConversationMessage.objects.create(session=session, role='assistant', content=reply_text, metadata={'payload': reply_payload})

        return Response({'session_id': session.id, 'reply': reply_text, 'mode': session.mode, 'context': session.context_state})


def build_reply_text(payload, mode='concise') -> str:
    t = payload.get('type')
    d = payload.get('data', {})
    if t == 'meal_plan_today':
        meals = d.get('meals') or []
        lines = ["Today\'s meal plan:"]
        for m in meals:
            title = m.get('title') or m.get('name') or 'Meal'
            mt = (m.get('type') or '').title()
            kcal = m.get('nutrition', {}).get('calories') if isinstance(m.get('nutrition'), dict) else None
            lines.append(f"- {mt}: {title}" + (f" ({kcal} kcal)" if kcal else ''))
        return "\n".join(lines) if mode == 'concise' else "\n".join([lines[0], *lines[1:]])
    if t == 'meal_plan_week':
        days = d.get('days') or {}
        out = []
        for day, info in days.items():
            out.append(f"{str(day)}:")
            for m in (info.get('meals') or []):
                title = m.get('title') or 'Meal'
                mt = (m.get('type') or '').title()
                out.append(f"- {mt}: {title}")
        return "\n".join(out)
    if t == 'recipe_prep':
        lines = [f"{d.get('title', 'Dinner')} - Ingredients and steps:"]
        ingredients = d.get('ingredients') or []
        for ing in ingredients:
            if isinstance(ing, dict):
                lines.append(f"- {ing.get('name')}: {ing.get('quantity')} {ing.get('unit')}")
            else:
                lines.append(f"- {ing}")
        steps = d.get('instructions') or []
        if isinstance(steps, list):
            for idx, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    lines.append(f"Step {idx}: {step.get('text') or step.get('instruction') or step}")
                else:
                    lines.append(f"Step {idx}: {step}")
        return "\n".join(lines)
    if t == 'protein_analysis':
        ok = d.get('meeting_target')
        status = 'on track' if ok else 'below target' if ok is False else 'no target set'
        return (f"Protein over last {d.get('period_days')} days: avg {d.get('average_protein_g_per_day')} g/day. "
                f"Target: {d.get('target_protein_g_per_day')} g/day. Status: {status}.")
    if t == 'weight_trend':
        trend = d.get('trend')
        return (f"Weight trend over {d.get('period_days')} days: from {d.get('start_weight_kg')} kg to {d.get('end_weight_kg')} kg "
                f"({d.get('change_kg')} kg change). Pattern: {trend}.")
    if t == 'goals':
        return f"Your primary fitness goal is {str(d.get('goal')).replace('_', ' ')}."
    if t == 'metrics_overview':
        name = d.get('name')
        parts = []
        if d.get('weight_kg') is not None:
            parts.append(f"weight {d['weight_kg']} kg")
        if d.get('bmi') is not None:
            parts.append(f"BMI {d['bmi']}")
        if d.get('wellness_score') is not None:
            parts.append(f"wellness score {d['wellness_score']}")
        if d.get('weekly_activity_sessions') is not None:
            parts.append(f"{d['weekly_activity_sessions']} activities this week")
        goal = str(d.get('goal') or '').replace('_', ' ')
        prefix = "Here\'s your current overview: " if mode == 'concise' else f"{name}, here\'s your current overview aligned with your goal of {goal}: "
        return prefix + ", ".join(parts)
    if t == 'wellness_focus':
        comp = d.get('lowest_component')
        return f"To improve your wellness score, focus on {comp}. {d.get('recommendation')}"
    return "I\'m here to help with your health metrics, meal plans, recipes, and nutrition analysis. Ask me anything."