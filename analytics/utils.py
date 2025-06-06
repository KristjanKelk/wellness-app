import json
import csv
import io
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from .models import HealthSummary, SummaryMetric
from health_profiles.models import HealthProfile, Activity, WeightHistory


class SummaryExportUtils:
    """Utilities for exporting health summaries in various formats"""

    @staticmethod
    def export_to_csv(user, summary_ids=None, start_date=None, end_date=None):
        """Export summaries to CSV format"""
        queryset = HealthSummary.objects.filter(user=user, status='completed')

        if summary_ids:
            queryset = queryset.filter(id__in=summary_ids)

        if start_date and end_date:
            queryset = queryset.filter(
                start_date__gte=start_date,
                end_date__lte=end_date
            )

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Summary ID', 'Type', 'Start Date', 'End Date', 'Created At',
            'Activity Count', 'Total Duration', 'Active Days', 'Milestones',
            'Wellness Score', 'Status', 'Key Achievements', 'Recommendations'
        ])

        # Write data
        for summary in queryset.order_by('-created_at'):
            metrics = summary.metrics_summary
            writer.writerow([
                summary.id,
                summary.summary_type,
                summary.start_date,
                summary.end_date,
                summary.created_at.strftime('%Y-%m-%d %H:%M'),
                metrics.get('activity_count', 0),
                metrics.get('total_duration', 0),
                metrics.get('active_days', 0),
                metrics.get('milestones_achieved', 0),
                metrics.get('wellness_score', ''),
                summary.status,
                '; '.join(summary.key_achievements or []),
                '; '.join(summary.recommendations or [])
            ])

        output.seek(0)
        return output.getvalue()

    @staticmethod
    def export_to_json(user, summary_ids=None, include_full_text=True):
        """Export summaries to JSON format"""
        queryset = HealthSummary.objects.filter(user=user, status='completed')

        if summary_ids:
            queryset = queryset.filter(id__in=summary_ids)

        export_data = {
            'export_date': timezone.now().isoformat(),
            'user_id': user.id,
            'username': user.username,
            'total_summaries': queryset.count(),
            'summaries': []
        }

        for summary in queryset.order_by('-created_at'):
            summary_data = {
                'id': summary.id,
                'summary_type': summary.summary_type,
                'start_date': summary.start_date.isoformat(),
                'end_date': summary.end_date.isoformat(),
                'created_at': summary.created_at.isoformat(),
                'metrics_summary': summary.metrics_summary,
                'key_achievements': summary.key_achievements,
                'areas_for_improvement': summary.areas_for_improvement,
                'recommendations': summary.recommendations,
                'status': summary.status
            }

            if include_full_text:
                summary_data['summary_text'] = summary.summary_text

            # Include detailed metrics
            detailed_metrics = []
            for metric in summary.detailed_metrics.all():
                detailed_metrics.append({
                    'metric_name': metric.metric_name,
                    'metric_value': float(metric.metric_value),
                    'metric_unit': metric.metric_unit,
                    'previous_value': float(metric.previous_value) if metric.previous_value else None,
                    'change_percentage': float(metric.change_percentage) if metric.change_percentage else None,
                    'change_direction': metric.change_direction
                })

            summary_data['detailed_metrics'] = detailed_metrics
            export_data['summaries'].append(summary_data)

        return json.dumps(export_data, indent=2)


class SummaryVisualizationUtils:
    """Utilities for creating visualizations of health summary data"""

    @staticmethod
    def create_progress_chart(user, weeks=12):
        """Create a progress chart showing wellness scores over time"""
        # Get recent summaries
        cutoff_date = timezone.now() - timedelta(weeks=weeks)
        summaries = HealthSummary.objects.filter(
            user=user,
            summary_type='weekly',
            status='completed',
            created_at__gte=cutoff_date
        ).order_by('start_date')

        if not summaries.exists():
            return None

        # Extract data
        dates = []
        wellness_scores = []
        activity_counts = []

        for summary in summaries:
            dates.append(summary.start_date)
            wellness_scores.append(summary.metrics_summary.get('wellness_score', 0))
            activity_counts.append(summary.metrics_summary.get('activity_count', 0))

        # Create chart
        plt.style.use('seaborn-v0_8')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Wellness score chart
        ax1.plot(dates, wellness_scores, marker='o', linewidth=2, markersize=6, color='#4CAF50')
        ax1.set_ylabel('Wellness Score')
        ax1.set_title(f'Health Progress Over Last {weeks} Weeks')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)

        # Activity count chart
        ax2.bar(dates, activity_counts, alpha=0.7, color='#2196F3')
        ax2.set_ylabel('Weekly Activities')
        ax2.set_xlabel('Week Starting')
        ax2.grid(True, alpha=0.3)

        # Format dates
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)

        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f"data:image/png;base64,{chart_base64}"

    @staticmethod
    def create_achievement_distribution_chart(user):
        """Create a chart showing distribution of achievement themes"""
        summaries = HealthSummary.objects.filter(user=user, status='completed')

        if not summaries.exists():
            return None

        # Extract achievement themes
        all_achievements = []
        for summary in summaries:
            all_achievements.extend(summary.key_achievements or [])

        if not all_achievements:
            return None

        # Simple keyword extraction and counting
        from collections import Counter
        import re

        words = []
        for achievement in all_achievements:
            # Extract meaningful words
            achievement_words = re.findall(r'\b\w+\b', achievement.lower())
            meaningful_words = [
                word for word in achievement_words
                if len(word) > 3 and word not in [
                    'achieved', 'completed', 'reached', 'maintained', 'improved'
                ]
            ]
            words.extend(meaningful_words)

        # Get top themes
        word_counts = Counter(words)
        top_themes = word_counts.most_common(8)

        if not top_themes:
            return None

        # Create chart
        themes, counts = zip(*top_themes)

        plt.figure(figsize=(10, 6))
        plt.bar(themes, counts, color='#4CAF50', alpha=0.8)
        plt.title('Most Common Achievement Themes')
        plt.xlabel('Theme')
        plt.ylabel('Frequency')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)

        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f"data:image/png;base64,{chart_base64}"


class SummaryAnalyticsUtils:
    """Advanced analytics utilities for health summaries"""

    @staticmethod
    def calculate_consistency_metrics(user):
        """Calculate various consistency metrics for a user"""
        # Get all completed summaries
        summaries = HealthSummary.objects.filter(user=user, status='completed').order_by('start_date')

        if summaries.count() < 2:
            return None

        # Calculate streak metrics
        weekly_summaries = summaries.filter(summary_type='weekly')
        monthly_summaries = summaries.filter(summary_type='monthly')

        # Calculate current streaks
        weekly_streak = SummaryAnalyticsUtils._calculate_streak(weekly_summaries, 'weekly')
        monthly_streak = SummaryAnalyticsUtils._calculate_streak(monthly_summaries, 'monthly')

        # Calculate average time between summaries
        time_gaps = []
        for i in range(1, summaries.count()):
            gap = (summaries[i].created_at - summaries[i - 1].created_at).days
            time_gaps.append(gap)

        avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 0

        # Calculate improvement trends
        wellness_scores = [
            s.metrics_summary.get('wellness_score', 0)
            for s in summaries
            if s.metrics_summary.get('wellness_score')
        ]

        improvement_trend = 'stable'
        if len(wellness_scores) >= 3:
            recent_avg = sum(wellness_scores[-3:]) / 3
            older_avg = sum(wellness_scores[:3]) / 3

            if recent_avg > older_avg + 5:
                improvement_trend = 'improving'
            elif recent_avg < older_avg - 5:
                improvement_trend = 'declining'

        return {
            'total_summaries': summaries.count(),
            'weekly_streak': weekly_streak,
            'monthly_streak': monthly_streak,
            'average_gap_days': round(avg_gap, 1),
            'improvement_trend': improvement_trend,
            'consistency_score': min(100, (weekly_streak * 5) + (monthly_streak * 10)),
            'first_summary_date': summaries.first().created_at.date(),
            'latest_summary_date': summaries.last().created_at.date()
        }

    @staticmethod
    def _calculate_streak(summaries, summary_type):
        """Calculate current streak for a specific summary type"""
        if not summaries.exists():
            return 0

        today = timezone.now().date()
        period_length = 7 if summary_type == 'weekly' else 30  # Approximate

        streak = 0
        current_date = today

        # Go backwards from today
        for _ in range(52):  # Max 1 year
            # Calculate expected period for current_date
            if summary_type == 'weekly':
                week_start = current_date - timedelta(days=current_date.weekday())
                week_end = week_start + timedelta(days=6)

                has_summary = summaries.filter(
                    start_date=week_start,
                    end_date=week_end
                ).exists()
            else:  # monthly
                month_start = current_date.replace(day=1)
                if current_date.month == 12:
                    month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

                has_summary = summaries.filter(
                    start_date=month_start,
                    end_date=month_end
                ).exists()

            if has_summary:
                streak += 1
                current_date -= timedelta(days=period_length)
            else:
                break

        return streak

    @staticmethod
    def get_summary_insights(user):
        """Get comprehensive insights about user's summary patterns"""
        summaries = HealthSummary.objects.filter(user=user, status='completed')

        if not summaries.exists():
            return None

        # Basic metrics
        total_summaries = summaries.count()
        weekly_count = summaries.filter(summary_type='weekly').count()
        monthly_count = summaries.filter(summary_type='monthly').count()

        # Time-based analysis
        first_summary = summaries.order_by('created_at').first()
        days_since_first = (timezone.now().date() - first_summary.created_at.date()).days

        # Achievement analysis
        all_achievements = []
        all_improvements = []
        total_milestones = 0

        for summary in summaries:
            all_achievements.extend(summary.key_achievements or [])
            all_improvements.extend(summary.areas_for_improvement or [])
            total_milestones += summary.metrics_summary.get('milestones_achieved', 0)

        # Most productive periods
        best_week = summaries.filter(summary_type='weekly').order_by(
            '-metrics_summary__activity_count'
        ).first()

        best_month = summaries.filter(summary_type='monthly').order_by(
            '-metrics_summary__total_duration'
        ).first()

        return {
            'overview': {
                'total_summaries': total_summaries,
                'weekly_summaries': weekly_count,
                'monthly_summaries': monthly_count,
                'days_tracking': days_since_first,
                'total_achievements': len(all_achievements),
                'total_milestones': total_milestones
            },
            'productivity': {
                'best_week': {
                    'period': f"{best_week.start_date} to {best_week.end_date}",
                    'activities': best_week.metrics_summary.get('activity_count', 0)
                } if best_week else None,
                'best_month': {
                    'period': f"{best_month.start_date} to {best_month.end_date}",
                    'duration': best_month.metrics_summary.get('total_duration', 0)
                } if best_month else None
            },
            'consistency': SummaryAnalyticsUtils.calculate_consistency_metrics(user),
            'patterns': {
                'avg_activities_per_week': SummaryAnalyticsUtils._calculate_average_metric(
                    summaries.filter(summary_type='weekly'), 'activity_count'
                ),
                'avg_duration_per_week': SummaryAnalyticsUtils._calculate_average_metric(
                    summaries.filter(summary_type='weekly'), 'total_duration'
                ),
                'milestone_frequency': total_milestones / total_summaries if total_summaries > 0 else 0
            }
        }

    @staticmethod
    def _calculate_average_metric(summaries, metric_name):
        """Calculate average value for a specific metric across summaries"""
        values = [
            s.metrics_summary.get(metric_name, 0)
            for s in summaries
            if s.metrics_summary.get(metric_name) is not None
        ]

        return sum(values) / len(values) if values else 0


class SummaryComparisonUtils:
    """Utilities for comparing summaries across different periods"""

    @staticmethod
    def compare_user_progress(user, period1_start, period1_end, period2_start, period2_end):
        """Compare user progress between two time periods"""

        period1_summaries = HealthSummary.objects.filter(
            user=user,
            status='completed',
            start_date__gte=period1_start,
            end_date__lte=period1_end
        )

        period2_summaries = HealthSummary.objects.filter(
            user=user,
            status='completed',
            start_date__gte=period2_start,
            end_date__lte=period2_end
        )

        def aggregate_period_data(summaries):
            if not summaries.exists():
                return None

            total_activities = sum(s.metrics_summary.get('activity_count', 0) for s in summaries)
            total_duration = sum(s.metrics_summary.get('total_duration', 0) for s in summaries)
            total_milestones = sum(s.metrics_summary.get('milestones_achieved', 0) for s in summaries)

            wellness_scores = [
                s.metrics_summary.get('wellness_score', 0)
                for s in summaries
                if s.metrics_summary.get('wellness_score')
            ]
            avg_wellness = sum(wellness_scores) / len(wellness_scores) if wellness_scores else 0

            return {
                'total_activities': total_activities,
                'total_duration': total_duration,
                'total_milestones': total_milestones,
                'average_wellness_score': round(avg_wellness, 1),
                'summary_count': summaries.count()
            }

        period1_data = aggregate_period_data(period1_summaries)
        period2_data = aggregate_period_data(period2_summaries)

        if not period1_data or not period2_data:
            return None

        # Calculate improvements
        improvements = {}
        for metric in period1_data:
            if metric != 'summary_count':
                p1_val = period1_data[metric]
                p2_val = period2_data[metric]

                if p2_val == 0:
                    change_percent = 100 if p1_val > 0 else 0
                else:
                    change_percent = ((p1_val - p2_val) / p2_val) * 100

                improvements[metric] = {
                    'previous': p2_val,
                    'current': p1_val,
                    'change': p1_val - p2_val,
                    'change_percent': round(change_percent, 1),
                    'improved': p1_val > p2_val
                }

        return {
            'period1': {
                'start_date': period1_start,
                'end_date': period1_end,
                'data': period1_data
            },
            'period2': {
                'start_date': period2_start,
                'end_date': period2_end,
                'data': period2_data
            },
            'improvements': improvements,
            'overall_improvement': sum(1 for imp in improvements.values() if imp['improved']) / len(improvements)
        }
