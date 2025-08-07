# ai_assistant/visualization_service.py
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Sum, Count
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

from health_profiles.models import WeightHistory, Activity
from meal_planning.models import NutritionLog
from analytics.models import WellnessScore


class VisualizationService:
    """Service for generating data visualizations based on natural language requests"""
    
    def __init__(self, user):
        self.user = user
        self.health_profile = getattr(user, 'health_profile', None)
        self.nutrition_profile = getattr(user, 'nutrition_profile', None)
    
    def generate_chart(self, request_type: str, time_period: str = "month") -> Dict[str, Any]:
        """Generate chart based on request type"""
        request_lower = request_type.lower()
        
        # Determine chart type based on request
        if "weight" in request_lower and ("trend" in request_lower or "change" in request_lower):
            return self._generate_weight_trend_chart(time_period)
        elif "protein" in request_lower and ("compare" in request_lower or "target" in request_lower):
            return self._generate_protein_comparison_chart(time_period)
        elif "macronutrient" in request_lower or "macro" in request_lower:
            return self._generate_macronutrient_breakdown_chart()
        elif "activity" in request_lower or "exercise" in request_lower:
            return self._generate_activity_chart(time_period)
        elif "wellness" in request_lower and "score" in request_lower:
            return self._generate_wellness_score_chart(time_period)
        elif "calorie" in request_lower:
            return self._generate_calorie_trend_chart(time_period)
        else:
            return {"error": "Unable to determine chart type from request"}
    
    def _generate_weight_trend_chart(self, time_period: str) -> Dict[str, Any]:
        """Generate weight trend line chart"""
        if not self.health_profile:
            return {"error": "No health profile found"}
        
        # Determine date range
        end_date = timezone.now()
        if time_period == "week":
            start_date = end_date - timedelta(days=7)
        elif time_period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=90)
        
        # Get weight history
        weights = WeightHistory.objects.filter(
            health_profile=self.health_profile,
            recorded_at__gte=start_date
        ).order_by('recorded_at')
        
        if not weights.exists():
            return {"error": "No weight data available for the specified period"}
        
        # Create line chart
        dates = [w.recorded_at.strftime('%Y-%m-%d') for w in weights]
        values = [float(w.weight_kg) for w in weights]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='Weight',
            line=dict(color='#4F46E5', width=3),
            marker=dict(size=8)
        ))
        
        # Add target weight line if exists
        if self.health_profile.target_weight_kg:
            fig.add_hline(
                y=float(self.health_profile.target_weight_kg),
                line_dash="dash",
                line_color="red",
                annotation_text="Target Weight"
            )
        
        fig.update_layout(
            title=f"Weight Trend - Last {time_period.capitalize()}",
            xaxis_title="Date",
            yaxis_title="Weight (kg)",
            template="plotly_white",
            height=400
        )
        
        return {
            "chart_type": "line",
            "chart_config": json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)),
            "summary": f"Weight changed from {values[0]:.1f}kg to {values[-1]:.1f}kg ({values[-1] - values[0]:+.1f}kg)"
        }
    
    def _generate_protein_comparison_chart(self, time_period: str) -> Dict[str, Any]:
        """Generate protein intake vs target comparison chart"""
        if not self.nutrition_profile:
            return {"error": "No nutrition profile found"}
        
        # Determine date range
        end_date = timezone.now().date()
        if time_period == "week":
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get nutrition logs
        logs = NutritionLog.objects.filter(
            user=self.user,
            date__range=[start_date, end_date]
        ).values('date').annotate(
            total_protein=Sum('protein')
        ).order_by('date')
        
        if not logs:
            return {"error": "No nutrition data available for the specified period"}
        
        # Create bar chart
        dates = [log['date'].strftime('%Y-%m-%d') for log in logs]
        protein_values = [float(log['total_protein'] or 0) for log in logs]
        target_values = [float(self.nutrition_profile.protein_target)] * len(dates)
        
        fig = go.Figure()
        
        # Actual protein intake
        fig.add_trace(go.Bar(
            x=dates,
            y=protein_values,
            name='Actual Intake',
            marker_color='#3B82F6'
        ))
        
        # Target line
        fig.add_trace(go.Scatter(
            x=dates,
            y=target_values,
            mode='lines',
            name='Target',
            line=dict(color='#EF4444', width=3, dash='dash')
        ))
        
        fig.update_layout(
            title=f"Protein Intake vs Target - Last {time_period.capitalize()}",
            xaxis_title="Date",
            yaxis_title="Protein (g)",
            template="plotly_white",
            height=400,
            showlegend=True
        )
        
        avg_protein = sum(protein_values) / len(protein_values) if protein_values else 0
        return {
            "chart_type": "bar",
            "chart_config": json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)),
            "summary": f"Average protein intake: {avg_protein:.1f}g/day (Target: {self.nutrition_profile.protein_target}g)"
        }
    
    def _generate_macronutrient_breakdown_chart(self) -> Dict[str, Any]:
        """Generate macronutrient breakdown pie chart for today"""
        if not self.user:
            return {"error": "User not found"}
        
        # Get today's nutrition logs
        today = timezone.now().date()
        logs = NutritionLog.objects.filter(
            user=self.user,
            date=today
        ).aggregate(
            total_protein=Sum('protein'),
            total_carbs=Sum('carbs'),
            total_fat=Sum('fat')
        )
        
        protein = float(logs['total_protein'] or 0)
        carbs = float(logs['total_carbs'] or 0)
        fat = float(logs['total_fat'] or 0)
        
        if protein == 0 and carbs == 0 and fat == 0:
            return {"error": "No nutrition data available for today"}
        
        # Create pie chart
        labels = ['Protein', 'Carbohydrates', 'Fat']
        values = [protein, carbs, fat]
        colors = ['#3B82F6', '#10B981', '#F59E0B']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title="Macronutrient Breakdown - Today",
            template="plotly_white",
            height=400,
            showlegend=True
        )
        
        total_grams = protein + carbs + fat
        return {
            "chart_type": "pie",
            "chart_config": json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)),
            "summary": f"Total macros: {total_grams:.1f}g (Protein: {protein:.1f}g, Carbs: {carbs:.1f}g, Fat: {fat:.1f}g)"
        }
    
    def _generate_activity_chart(self, time_period: str) -> Dict[str, Any]:
        """Generate activity summary chart"""
        if not self.health_profile:
            return {"error": "No health profile found"}
        
        # Determine date range
        end_date = timezone.now()
        if time_period == "week":
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get activities grouped by type
        activities = Activity.objects.filter(
            health_profile=self.health_profile,
            performed_at__gte=start_date
        ).values('activity_type').annotate(
            total_duration=Sum('duration_minutes'),
            count=Count('id')
        )
        
        if not activities:
            return {"error": "No activity data available for the specified period"}
        
        # Create bar chart
        activity_types = [a['activity_type'] for a in activities]
        durations = [a['total_duration'] for a in activities]
        
        fig = go.Figure(data=[
            go.Bar(
                x=activity_types,
                y=durations,
                text=[f"{d} min" for d in durations],
                textposition='auto',
                marker_color='#8B5CF6'
            )
        ])
        
        fig.update_layout(
            title=f"Activity Summary - Last {time_period.capitalize()}",
            xaxis_title="Activity Type",
            yaxis_title="Total Duration (minutes)",
            template="plotly_white",
            height=400
        )
        
        total_duration = sum(durations)
        total_sessions = sum(a['count'] for a in activities)
        
        return {
            "chart_type": "bar",
            "chart_config": json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)),
            "summary": f"Total: {total_duration} minutes across {total_sessions} sessions"
        }
    
    def _generate_wellness_score_chart(self, time_period: str) -> Dict[str, Any]:
        """Generate wellness score trend chart"""
        if not self.health_profile:
            return {"error": "No health profile found"}
        
        # Determine date range
        end_date = timezone.now()
        if time_period == "week":
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get wellness scores
        scores = WellnessScore.objects.filter(
            health_profile=self.health_profile,
            calculated_at__gte=start_date
        ).order_by('calculated_at')
        
        if not scores:
            return {"error": "No wellness score data available for the specified period"}
        
        # Create line chart with multiple traces
        dates = [s.calculated_at.strftime('%Y-%m-%d') for s in scores]
        
        fig = go.Figure()
        
        # Total score
        fig.add_trace(go.Scatter(
            x=dates,
            y=[s.total_score for s in scores],
            mode='lines+markers',
            name='Total Score',
            line=dict(color='#4F46E5', width=3)
        ))
        
        # Component scores
        fig.add_trace(go.Scatter(
            x=dates,
            y=[s.activity_score for s in scores],
            mode='lines',
            name='Activity',
            line=dict(color='#3B82F6', width=2, dash='dot')
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=[s.nutrition_score for s in scores],
            mode='lines',
            name='Nutrition',
            line=dict(color='#10B981', width=2, dash='dot')
        ))
        
        fig.update_layout(
            title=f"Wellness Score Trend - Last {time_period.capitalize()}",
            xaxis_title="Date",
            yaxis_title="Score",
            template="plotly_white",
            height=400,
            showlegend=True,
            yaxis=dict(range=[0, 100])
        )
        
        latest_score = scores.last()
        return {
            "chart_type": "line",
            "chart_config": json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)),
            "summary": f"Current wellness score: {latest_score.total_score}/100"
        }
    
    def _generate_calorie_trend_chart(self, time_period: str) -> Dict[str, Any]:
        """Generate calorie intake trend chart"""
        if not self.nutrition_profile:
            return {"error": "No nutrition profile found"}
        
        # Determine date range
        end_date = timezone.now().date()
        if time_period == "week":
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get daily calorie totals
        logs = NutritionLog.objects.filter(
            user=self.user,
            date__range=[start_date, end_date]
        ).values('date').annotate(
            total_calories=Sum('calories')
        ).order_by('date')
        
        if not logs:
            return {"error": "No calorie data available for the specified period"}
        
        # Create combination chart
        dates = [log['date'].strftime('%Y-%m-%d') for log in logs]
        calorie_values = [float(log['total_calories'] or 0) for log in logs]
        target_values = [float(self.nutrition_profile.calorie_target)] * len(dates)
        
        fig = go.Figure()
        
        # Actual calories as bars
        fig.add_trace(go.Bar(
            x=dates,
            y=calorie_values,
            name='Actual Intake',
            marker_color=['#10B981' if c <= self.nutrition_profile.calorie_target * 1.1 
                         else '#F59E0B' for c in calorie_values]
        ))
        
        # Target line
        fig.add_trace(go.Scatter(
            x=dates,
            y=target_values,
            mode='lines',
            name='Target',
            line=dict(color='#EF4444', width=3, dash='dash')
        ))
        
        fig.update_layout(
            title=f"Calorie Intake vs Target - Last {time_period.capitalize()}",
            xaxis_title="Date",
            yaxis_title="Calories",
            template="plotly_white",
            height=400,
            showlegend=True
        )
        
        avg_calories = sum(calorie_values) / len(calorie_values) if calorie_values else 0
        adherence_days = sum(1 for c in calorie_values 
                           if self.nutrition_profile.calorie_target * 0.9 <= c <= self.nutrition_profile.calorie_target * 1.1)
        
        return {
            "chart_type": "bar",
            "chart_config": json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)),
            "summary": f"Average: {avg_calories:.0f} cal/day | On target {adherence_days}/{len(calorie_values)} days"
        }
    
    def suggest_visualization(self, context: str) -> List[Dict[str, str]]:
        """Suggest relevant visualizations based on conversation context"""
        suggestions = []
        context_lower = context.lower()
        
        if "weight" in context_lower or "bmi" in context_lower:
            suggestions.append({
                "type": "weight_trend",
                "prompt": "Would you like to see a chart of your weight trend over the past month?",
                "description": "Visualize how your weight has changed over time"
            })
        
        if "protein" in context_lower or "nutrition" in context_lower:
            suggestions.append({
                "type": "protein_comparison",
                "prompt": "Would you like to see how your protein intake compares to your target?",
                "description": "Compare your actual protein consumption with your daily goals"
            })
            suggestions.append({
                "type": "macronutrient_breakdown",
                "prompt": "Would you like to see a breakdown of your macronutrients for today?",
                "description": "View the proportions of protein, carbs, and fats in your diet"
            })
        
        if "calorie" in context_lower or "diet" in context_lower:
            suggestions.append({
                "type": "calorie_trend",
                "prompt": "Would you like to see your calorie intake trend this week?",
                "description": "Track how well you're meeting your daily calorie targets"
            })
        
        if "activity" in context_lower or "exercise" in context_lower:
            suggestions.append({
                "type": "activity_summary",
                "prompt": "Would you like to see a summary of your activities this week?",
                "description": "View your exercise patterns and total activity duration"
            })
        
        if "wellness" in context_lower or "progress" in context_lower:
            suggestions.append({
                "type": "wellness_score",
                "prompt": "Would you like to see your wellness score trend?",
                "description": "Track your overall wellness progress over time"
            })
        
        return suggestions[:2]  # Return top 2 suggestions