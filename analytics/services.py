# analytics/services.py - Fixed with proper imports
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Sum
import logging

# Import the models that are used in this file
from .models import Milestone, WellnessScore
from health_profiles.models import HealthProfile, WeightHistory, Activity

# Import nutrition models for enhanced wellness scoring
try:
    from meal_planning.models import NutritionProfile, NutritionLog
    NUTRITION_AVAILABLE = True
except ImportError:
    NUTRITION_AVAILABLE = False

logger = logging.getLogger(__name__)

class MilestoneService:
    @staticmethod
    def check_weight_milestone(user):
        """
        Check if user has achieved a weight milestone (every 5% towards goal)
        """
        try:
            profile = HealthProfile.objects.get(user=user)

            # Only proceed if user has a target weight
            if not profile.target_weight_kg or not profile.weight_kg:
                return None

            # Calculate starting weight (either from history or current weight)
            weight_history = WeightHistory.objects.filter(health_profile=profile).order_by('recorded_at')
            starting_weight = weight_history.first().weight_kg if weight_history.exists() else profile.weight_kg

            # Calculate current progress percentage
            target_weight = Decimal(profile.target_weight_kg)
            current_weight = Decimal(profile.weight_kg)
            total_change_needed = starting_weight - target_weight

            # Avoid division by zero and handle if already at goal
            if total_change_needed == 0:
                return None

            # First check if the goal has been reached (within 0.5 kg tolerance)
            if abs(current_weight - target_weight) <= 0.5:
                # Check if we already have a weight goal achievement milestone
                existing_milestone = Milestone.objects.filter(
                    user=user,
                    milestone_type='weight',
                    description__contains='Reached weight goal'
                ).exists()

                if not existing_milestone:
                    # Create the milestone
                    milestone = Milestone.objects.create(
                        user=user,
                        milestone_type='weight',
                        description=f"Reached weight goal of {float(target_weight)} kg!",
                        progress_value=float(current_weight),
                        progress_percentage=100  # 100% achievement
                    )
                    return milestone

            # If goal not reached yet, check for progress milestones
            # Weight loss goal
            if starting_weight > target_weight:
                current_change = starting_weight - current_weight
                progress_percentage = (current_change / abs(total_change_needed)) * 100
            # Weight gain goal
            else:
                current_change = current_weight - starting_weight
                progress_percentage = (current_change / abs(total_change_needed)) * 100

            # Check if the progress percentage crosses a 5% threshold
            milestone_thresholds = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
            for threshold in milestone_thresholds:
                # Check if we just crossed this threshold
                if progress_percentage >= threshold:
                    # See if we already recorded this milestone
                    existing_milestone = Milestone.objects.filter(
                        user=user,
                        milestone_type='weight',
                        progress_percentage=threshold
                    ).exists()

                    if not existing_milestone:
                        # Create new milestone
                        milestone = Milestone.objects.create(
                            user=user,
                            milestone_type='weight',
                            description=f"Reached {threshold}% of weight goal!",
                            progress_value=float(current_weight),
                            progress_percentage=threshold
                        )
                        return milestone

            return None

        except HealthProfile.DoesNotExist:
            return None

    @staticmethod
    def check_activity_milestone(user, new_activity_days):
        """
        Check if user has achieved an activity milestone (additional day per week)
        """
        try:
            profile = HealthProfile.objects.get(user=user)

            # If we don't have activity data, we can't track milestones
            if profile.weekly_activity_days is None:
                profile.weekly_activity_days = new_activity_days
                profile.save(update_fields=['weekly_activity_days'])
                return None

            # Check if activity days increased
            if new_activity_days > profile.weekly_activity_days:
                # Create milestone
                milestone = Milestone.objects.create(
                    user=user,
                    milestone_type='activity',
                    description=f"Increased weekly activity to {new_activity_days} days!",
                    progress_value=new_activity_days,
                    progress_percentage=(new_activity_days / 7) * 100
                )

                # Update the profile with new activity days
                profile.weekly_activity_days = new_activity_days
                profile.save(update_fields=['weekly_activity_days'])

                return milestone

            return None

        except HealthProfile.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error checking activity milestone for user {user.id}: {str(e)}")
            return None

    @staticmethod
    def check_habit_streak(user, habit_name, current_streak):
        """
        Check if user has achieved a habit streak milestone
        """
        try:
            # Streak milestones at 3, 7, 14, 21, 30, 60, 90, 180, 365 days
            streak_milestones = [3, 7, 14, 21, 30, 60, 90, 180, 365]

            for milestone_streak in streak_milestones:
                if current_streak == milestone_streak:
                    # Create milestone
                    milestone = Milestone.objects.create(
                        user=user,
                        milestone_type='habit',
                        description=f"{milestone_streak}-day streak for {habit_name}!",
                        progress_value=current_streak,
                        progress_percentage=None  # No percentage for streaks
                    )
                    return milestone

            return None
        except Exception as e:
            logger.error(f"Error checking habit streak for user {user.id}: {str(e)}")
            return None

    @staticmethod
    def update_progress_score(user):
        """
        Update the wellness score based on milestone achievements
        """
        try:
            # Get the most recent wellness score
            profile = HealthProfile.objects.get(user=user)
            wellness_score = WellnessScore.objects.filter(health_profile=profile).order_by('-created_at').first()

            if not wellness_score:
                return None

            # Calculate milestones_achieved in the last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_milestones = Milestone.objects.filter(
                user=user,
                achieved_at__gte=thirty_days_ago
            ).count()

            # Adjust progress score based on milestones (max 100)
            milestone_bonus = min(recent_milestones * 5, 50)  # Each milestone worth 5 points, up to 50

            # Base progress score (from whatever existing logic)
            base_progress_score = 50

            # New progress score with milestone bonus
            new_progress_score = min(base_progress_score + milestone_bonus, 100)

            # Update wellness score
            wellness_score.progress_score = new_progress_score
            wellness_score.calculate_total()
            wellness_score.save()

            return wellness_score

        except HealthProfile.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error updating progress score for user {user.id}: {str(e)}")
            return None

    @staticmethod
    def check_weight_logging_streak(user):
        """
        Check if user has achieved a streak for consistently logging weight
        """
        try:
            profile = HealthProfile.objects.get(user=user)
            weight_entries = WeightHistory.objects.filter(health_profile=profile).order_by('recorded_at')

            if not weight_entries or weight_entries.count() < 3:
                return None  # Need at least 3 entries to consider a streak

            # Calculate the streak by checking for daily entries
            streak = 1
            max_streak = 1

            for i in range(1, len(weight_entries)):
                current_date = weight_entries[i].recorded_at.date()
                prev_date = weight_entries[i - 1].recorded_at.date()

                # If entries are on consecutive days
                if (current_date - prev_date).days == 1:
                    streak += 1
                    max_streak = max(max_streak, streak)
                # If same day entries, ignore
                elif (current_date - prev_date).days == 0:
                    continue
                # If gap in days, reset streak
                else:
                    streak = 1

            # Check if current streak matches milestone thresholds
            streak_milestones = [3, 7, 14, 21, 30]

            if max_streak in streak_milestones:
                # Check if we already have this milestone
                existing_milestone = Milestone.objects.filter(
                    user=user,
                    milestone_type='habit',
                    description__contains=f"{max_streak}-day streak for weight logging"
                ).exists()

                if not existing_milestone:
                    milestone = Milestone.objects.create(
                        user=user,
                        milestone_type='habit',
                        description=f"{max_streak}-day streak for weight logging!",
                        progress_value=max_streak,
                        progress_percentage=None
                    )
                    return milestone

            return None

        except HealthProfile.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error checking weight logging streak for user {user.id}: {str(e)}")
            return None

    @staticmethod
    def check_activity_milestone_by_count(user):
        """
        Check if user has achieved an activity count milestone
        """
        try:
            profile = HealthProfile.objects.get(user=user)
            activity_count = Activity.objects.filter(health_profile=profile).count()
            count_milestones = [1, 5, 10, 25, 50, 100, 250, 500, 1000]

            for count in count_milestones:
                if activity_count == count:
                    existing_milestone = Milestone.objects.filter(
                        user=user,
                        milestone_type='activity',
                        description__contains=f"{count} activities"
                    ).exists()

                    if not existing_milestone:
                        milestone = Milestone.objects.create(
                            user=user,
                            milestone_type='activity',
                            description=f"Completed {count} activities!",
                            progress_value=count,
                            progress_percentage=None  # Not applicable for count milestones
                        )
                        return milestone

            return None

        except HealthProfile.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error checking activity count milestone for user {user.id}: {str(e)}")
            return None


class WellnessScoreService:
    """
    Enhanced wellness score calculation service
    Maintains backward compatibility with existing API structure
    """

    @staticmethod
    def calculate_comprehensive_score(health_profile, user):
        """
        Calculate detailed wellness score with all four components
        Returns: dict with individual scores and total
        """
        try:
            bmi_score = WellnessScoreService.calculate_bmi_score(health_profile)
            activity_score = WellnessScoreService.calculate_activity_score(health_profile, user)
            progress_score = WellnessScoreService.calculate_progress_score(health_profile, user)
            habits_score = WellnessScoreService.calculate_habits_score(health_profile, user)
            nutrition_score = WellnessScoreService.calculate_nutrition_score(health_profile, user)

            # Adjust weights to include nutrition component
            total_score = (
                    float(bmi_score) * 0.25 +
                    float(activity_score) * 0.25 +
                    float(progress_score) * 0.15 +
                    float(habits_score) * 0.15 +
                    float(nutrition_score) * 0.20
            )

            return {
                'bmi_score': round(bmi_score, 2),
                'activity_score': round(activity_score, 2),
                'progress_score': round(progress_score, 2),
                'habits_score': round(habits_score, 2),
                'nutrition_score': round(nutrition_score, 2),
                'total_score': round(total_score, 2)
            }

        except Exception as e:
            logger.error(f"Error calculating wellness score for user {user.id}: {str(e)}")
            return {
                'bmi_score': 50.0,
                'activity_score': 50.0,
                'progress_score': 50.0,
                'habits_score': 50.0,
                'nutrition_score': 50.0,
                'total_score': 50.0
            }

    @staticmethod
    def calculate_bmi_score(health_profile):
        """
        Enhanced BMI scoring with edge cases and realistic ranges
        Score range: 0-100 (100 = optimal BMI range)
        """
        bmi = health_profile.calculate_bmi()

        if not bmi or bmi <= 0:
            return 50.0  # Default score when BMI unavailable

        # Optimal BMI range: 18.5 - 24.9 gets full points
        if 18.5 <= bmi <= 24.9:
            # Within optimal range - score based on how close to center (21.7)
            distance_from_optimal = abs(bmi - 21.7)
            return max(95.0, 100.0 - (distance_from_optimal * 2))

        # Underweight scoring (BMI < 18.5)
        elif bmi < 18.5:
            if bmi < 15.0:  # Severely underweight
                return 20.0
            elif bmi < 16.5:  # Moderately underweight
                return 35.0
            else:  # Mildly underweight (16.5-18.5)
                # Linear decrease from 85 to 0 as BMI goes from 18.5 to 16.5
                return max(0.0, 85.0 - ((18.5 - bmi) * 42.5))

        # Overweight and obese scoring (BMI > 24.9)
        else:
            if bmi <= 29.9:  # Overweight (25.0-29.9)
                # Linear decrease from 85 to 60
                return max(60.0, 85.0 - ((bmi - 24.9) * 5))
            elif bmi <= 34.9:  # Class I obesity (30.0-34.9)
                # Linear decrease from 60 to 40
                return max(40.0, 60.0 - ((bmi - 29.9) * 4))
            elif bmi <= 39.9:  # Class II obesity (35.0-39.9)
                # Linear decrease from 40 to 25
                return max(25.0, 40.0 - ((bmi - 34.9) * 3))
            else:  # Class III obesity (40.0+)
                # Cap at minimum score for extreme obesity
                return max(15.0, 25.0 - ((bmi - 39.9) * 2))

    @staticmethod
    def calculate_activity_score(health_profile, user):
        """
        Sophisticated activity scoring based on multiple factors:
        - Base activity level (40% of score)
        - Recent logged activities (35% of score)
        - Activity consistency (25% of score)
        """
        try:
            # Base score from declared activity level (40% weight)
            activity_level_scores = {
                'sedentary': 25,  # Encourage movement
                'light': 45,  # Room for improvement
                'moderate': 70,  # Good baseline
                'active': 85,  # Very good
                'very_active': 95  # Excellent, leave room for logged activity bonus
            }
            base_score = activity_level_scores.get(health_profile.activity_level, 50)

            # Recent activity analysis (last 14 days for better pattern recognition)
            two_weeks_ago = timezone.now() - timedelta(days=14)
            recent_activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__gte=two_weeks_ago
            )

            # Activity volume score (35% weight) - based on frequency and duration
            activity_count = recent_activities.count()
            total_duration = recent_activities.aggregate(
                total=Sum('duration_minutes')
            )['total'] or 0

            # Score based on activity count (0-30 points)
            if activity_count == 0:
                volume_score = 0
            elif activity_count <= 3:
                volume_score = activity_count * 7  # 7, 14, 21
            elif activity_count <= 7:
                volume_score = 21 + ((activity_count - 3) * 4)  # 25, 29, 33, 37
            elif activity_count <= 14:
                volume_score = 37 + ((activity_count - 7) * 2)  # 39, 41, ..., 51
            else:
                volume_score = min(60, 51 + (activity_count - 14))  # Cap at 60

            # Duration bonus (0-15 points)
            if total_duration >= 300:  # 5+ hours in 2 weeks (excellent)
                duration_bonus = 15
            elif total_duration >= 180:  # 3+ hours (very good)
                duration_bonus = 12
            elif total_duration >= 120:  # 2+ hours (good)
                duration_bonus = 8
            elif total_duration >= 60:  # 1+ hour (fair)
                duration_bonus = 5
            else:
                duration_bonus = 0

            activity_volume_score = min(volume_score + duration_bonus, 75)

            # Consistency score (25% weight) - activity spread across days
            unique_activity_days = recent_activities.dates('performed_at', 'day').distinct().count()

            if unique_activity_days == 0:
                consistency_score = 0
            elif unique_activity_days <= 2:
                consistency_score = unique_activity_days * 8  # 8, 16
            elif unique_activity_days <= 5:
                consistency_score = 16 + ((unique_activity_days - 2) * 6)  # 22, 28, 34
            elif unique_activity_days <= 10:
                consistency_score = 34 + ((unique_activity_days - 5) * 4)  # 38, 42, 46, 50, 54
            else:
                consistency_score = min(65, 54 + (unique_activity_days - 10))  # Cap at 65

            # Combine all components
            # Base: 40%, Volume: 35%, Consistency: 25%
            final_score = (
                    (base_score * 0.4) +
                    (activity_volume_score * 0.35) +
                    (consistency_score * 0.25)
            )

            return min(100.0, max(0.0, final_score))

        except Exception as e:
            logger.error(f"Error calculating activity score: {str(e)}")
            # Fallback to basic activity level scoring
            activity_level_scores = {
                'sedentary': 20, 'light': 40, 'moderate': 60, 'active': 80, 'very_active': 90
            }
            return activity_level_scores.get(health_profile.activity_level, 50)

    @staticmethod
    def calculate_progress_score(health_profile, user):
        """
        Progress scoring based on goal achievements and milestones
        Considers recent achievements and goal proximity
        """
        try:
            base_score = 50.0  # Starting point

            # Recent milestones boost (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_milestones = Milestone.objects.filter(
                user=user,
                achieved_at__gte=thirty_days_ago
            )

            milestone_count = recent_milestones.count()

            # Milestone achievement bonus (up to 30 points)
            if milestone_count >= 5:
                milestone_bonus = 30  # Exceptional achievement
            elif milestone_count >= 3:
                milestone_bonus = 25  # Excellent progress
            elif milestone_count >= 2:
                milestone_bonus = 18  # Very good progress
            elif milestone_count >= 1:
                milestone_bonus = 12  # Good progress
            else:
                milestone_bonus = 0  # No recent achievements

            # Weight progress analysis (if weight goal exists)
            weight_progress_bonus = 0
            if health_profile.target_weight_kg and health_profile.weight_kg:
                weight_progress_bonus = WellnessScoreService._calculate_weight_progress_score(
                    health_profile
                )

            # Activity improvement trend (last 30 vs previous 30 days)
            activity_trend_bonus = WellnessScoreService._calculate_activity_trend_score(
                health_profile, user
            )

            # Combine progress components
            total_progress_score = (
                    base_score +
                    milestone_bonus +
                    weight_progress_bonus +
                    activity_trend_bonus
            )

            return min(100.0, max(0.0, total_progress_score))

        except Exception as e:
            logger.error(f"Error calculating progress score: {str(e)}")
            return 50.0

    @staticmethod
    def _calculate_weight_progress_score(health_profile):
        """Calculate weight progress component (max 15 points)"""
        try:
            current_weight = float(health_profile.weight_kg)
            target_weight = float(health_profile.target_weight_kg)

            # Get weight history to calculate starting point
            weight_history = WeightHistory.objects.filter(
                health_profile=health_profile
            ).order_by('recorded_at')

            if not weight_history.exists():
                return 0

            starting_weight = float(weight_history.first().weight_kg)
            total_change_needed = abs(starting_weight - target_weight)

            if total_change_needed == 0:
                return 15  # Already at goal

            # Calculate progress percentage
            current_change = abs(starting_weight - current_weight)
            progress_percentage = (current_change / total_change_needed) * 100

            # Convert to score (0-15 points)
            if progress_percentage >= 100:
                return 15  # Goal achieved
            elif progress_percentage >= 75:
                return 12  # Excellent progress
            elif progress_percentage >= 50:
                return 8  # Good progress
            elif progress_percentage >= 25:
                return 5  # Some progress
            elif progress_percentage >= 10:
                return 2  # Minimal progress
            else:
                return 0  # No significant progress

        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating weight progress score: {str(e)}")
            return 0

    @staticmethod
    def _calculate_activity_trend_score(health_profile, user):
        """Calculate activity improvement trend (max 5 points)"""
        try:
            now = timezone.now()
            thirty_days_ago = now - timedelta(days=30)
            sixty_days_ago = now - timedelta(days=60)

            # Recent 30 days activity
            recent_activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__gte=thirty_days_ago
            ).count()

            # Previous 30 days activity
            previous_activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__gte=sixty_days_ago,
                performed_at__lt=thirty_days_ago
            ).count()

            if previous_activities == 0:
                # If no previous activity, any current activity is improvement
                return 3 if recent_activities > 0 else 0

            # Calculate improvement percentage
            improvement = ((recent_activities - previous_activities) / previous_activities) * 100

            if improvement >= 50:
                return 5  # Significant improvement
            elif improvement >= 25:
                return 3  # Good improvement
            elif improvement >= 10:
                return 2  # Some improvement
            elif improvement >= 0:
                return 1  # Maintaining activity level
            else:
                return 0  # Declining activity

        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Error calculating activity trend score: {str(e)}")
            return 0

    @staticmethod
    def calculate_habits_score(health_profile, user):
        """
        Habits scoring based on consistency in health behaviors
        Factors: logging consistency, profile maintenance, activity regularity
        """
        try:
            base_score = 30.0  # Start with base points for having a profile

            # Profile completeness (20 points max)
            completeness_score = WellnessScoreService._calculate_profile_completeness(health_profile)

            # Logging consistency (30 points max)
            logging_consistency_score = WellnessScoreService._calculate_logging_consistency(
                health_profile, user
            )

            # Activity regularity (20 points max)
            activity_regularity_score = WellnessScoreService._calculate_activity_regularity(
                health_profile
            )

            # Combine all habit components
            total_habits_score = (
                    base_score +
                    completeness_score +
                    logging_consistency_score +
                    activity_regularity_score
            )

            return min(100.0, max(0.0, total_habits_score))

        except Exception as e:
            logger.error(f"Error calculating habits score: {str(e)}")
            return 50.0

    @staticmethod
    def _calculate_profile_completeness(health_profile):
        """Calculate profile completeness score (max 20 points)"""
        required_fields = [
            health_profile.age,
            health_profile.gender,
            health_profile.height_cm,
            health_profile.weight_kg,
            health_profile.activity_level,
            health_profile.fitness_goal,
        ]

        optional_fields = [
            health_profile.occupation_type,
            health_profile.target_weight_kg,
            health_profile.weekly_activity_days,
            health_profile.fitness_level,
            health_profile.preferred_environment,
            health_profile.time_preference,
            health_profile.dietary_preference,
        ]

        # Required fields are worth more
        required_completed = sum(1 for field in required_fields if field is not None and field != '')
        optional_completed = sum(1 for field in optional_fields if field is not None and field != '')

        required_score = (required_completed / len(required_fields)) * 15  # 15 points max
        optional_score = (optional_completed / len(optional_fields)) * 5  # 5 points max

        return required_score + optional_score

    @staticmethod
    def _calculate_logging_consistency(health_profile, user):
        """Calculate logging consistency score (max 30 points)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Weight logging consistency (15 points max)
        weight_entries = WeightHistory.objects.filter(
            health_profile=health_profile,
            recorded_at__gte=thirty_days_ago
        ).count()

        if weight_entries >= 8:  # 2+ times per week
            weight_score = 15
        elif weight_entries >= 4:  # Weekly
            weight_score = 12
        elif weight_entries >= 2:  # Bi-weekly
            weight_score = 8
        elif weight_entries >= 1:  # Monthly
            weight_score = 4
        else:
            weight_score = 0

        # Activity logging consistency (15 points max)
        activity_entries = Activity.objects.filter(
            health_profile=health_profile,
            performed_at__gte=thirty_days_ago
        ).count()

        if activity_entries >= 12:  # 3+ times per week
            activity_score = 15
        elif activity_entries >= 8:  # 2+ times per week
            activity_score = 12
        elif activity_entries >= 4:  # Weekly
            activity_score = 8
        elif activity_entries >= 2:  # Bi-weekly
            activity_score = 4
        elif activity_entries >= 1:  # At least once
            activity_score = 2
        else:
            activity_score = 0

        return weight_score + activity_score

    @staticmethod
    def _calculate_activity_regularity(health_profile):
        """Calculate activity regularity score (max 20 points)"""
        try:
            thirty_days_ago = timezone.now() - timedelta(days=30)

            # Get activities grouped by week
            activities = Activity.objects.filter(
                health_profile=health_profile,
                performed_at__gte=thirty_days_ago
            )

            if not activities.exists():
                return 0

            # Group activities by week
            weekly_counts = []
            for week in range(4):  # Last 4 weeks
                week_start = thirty_days_ago + timedelta(weeks=week)
                week_end = week_start + timedelta(days=7)
                week_count = activities.filter(
                    performed_at__gte=week_start,
                    performed_at__lt=week_end
                ).count()
                weekly_counts.append(week_count)

            # Calculate consistency (lower variance = higher score)
            if len(weekly_counts) > 1:
                avg_weekly = sum(weekly_counts) / len(weekly_counts)

                if avg_weekly == 0:
                    return 0

                # Calculate coefficient of variation (lower is better)
                variance = sum((x - avg_weekly) ** 2 for x in weekly_counts) / len(weekly_counts)
                std_dev = variance ** 0.5
                cv = std_dev / avg_weekly if avg_weekly > 0 else 1

                # Convert to score (lower CV = higher score)
                if cv <= 0.3:  # Very consistent
                    consistency_multiplier = 1.0
                elif cv <= 0.5:  # Fairly consistent
                    consistency_multiplier = 0.8
                elif cv <= 0.8:  # Somewhat consistent
                    consistency_multiplier = 0.6
                else:  # Inconsistent
                    consistency_multiplier = 0.4

                # Base score from average activity level
                if avg_weekly >= 3:
                    base_regularity = 20
                elif avg_weekly >= 2:
                    base_regularity = 15
                elif avg_weekly >= 1:
                    base_regularity = 10
                else:
                    base_regularity = 5

                return base_regularity * consistency_multiplier

            return 5  # Some activity but not enough data for consistency

        except Exception as e:
            logger.error(f"Error calculating activity regularity: {str(e)}")
            return 0

    @staticmethod
    def calculate_nutrition_score(health_profile, user):
        """
        Calculate nutrition score based on:
        - Having a nutrition profile (20 points)
        - Recent nutrition logging consistency (30 points)
        - Meeting nutrition goals (30 points)
        - Nutrition plan adherence (20 points)
        """
        try:
            if not NUTRITION_AVAILABLE:
                return 50.0  # Default score when nutrition module not available

            base_score = 0.0

            # Check if user has a nutrition profile (20 points)
            try:
                nutrition_profile = NutritionProfile.objects.get(user=user)
                base_score += 20.0
                
                # Recent nutrition logging (30 points max)
                thirty_days_ago = timezone.now() - timedelta(days=30)
                recent_logs = NutritionLog.objects.filter(
                    user=user,
                    date__gte=thirty_days_ago.date()
                ).count()
                
                if recent_logs >= 20:  # Daily logging
                    logging_score = 30.0
                elif recent_logs >= 15:  # Most days
                    logging_score = 25.0
                elif recent_logs >= 10:  # Half the days
                    logging_score = 20.0
                elif recent_logs >= 5:  # Some logging
                    logging_score = 15.0
                else:  # Minimal logging
                    logging_score = 5.0
                    
                base_score += logging_score

                # Goal achievement analysis (30 points max)
                # Check recent logs for goal adherence
                recent_week_logs = NutritionLog.objects.filter(
                    user=user,
                    date__gte=(timezone.now() - timedelta(days=7)).date()
                )
                
                if recent_week_logs.exists():
                    goal_adherence_score = 0.0
                    total_days = recent_week_logs.count()
                    
                    calorie_target = nutrition_profile.calorie_target
                    protein_target = nutrition_profile.protein_target
                    
                    on_target_days = 0
                    for log in recent_week_logs:
                        calorie_diff = abs((log.total_calories or 0) - calorie_target) / calorie_target if calorie_target > 0 else 1
                        protein_diff = abs((log.total_protein or 0) - protein_target) / protein_target if protein_target > 0 else 1
                        
                        # Consider "on target" if within 15% of goals
                        if calorie_diff <= 0.15 and protein_diff <= 0.20:
                            on_target_days += 1
                    
                    adherence_rate = on_target_days / total_days if total_days > 0 else 0
                    goal_adherence_score = adherence_rate * 30.0
                    
                    base_score += goal_adherence_score
                else:
                    base_score += 10.0  # Partial credit for having profile but no recent data

                # Nutrition profile completeness (20 points max)
                completeness_factors = [
                    nutrition_profile.calorie_target > 0,
                    nutrition_profile.protein_target > 0,
                    nutrition_profile.carb_target > 0,
                    nutrition_profile.fat_target > 0,
                    len(nutrition_profile.dietary_preferences or []) > 0,
                    nutrition_profile.meals_per_day > 0,
                ]
                
                completeness_score = (sum(completeness_factors) / len(completeness_factors)) * 20.0
                base_score += completeness_score

            except NutritionProfile.DoesNotExist:
                # No nutrition profile - encourage setup
                base_score = 25.0

            return min(100.0, max(0.0, base_score))

        except Exception as e:
            logger.error(f"Error calculating nutrition score: {str(e)}")
            return 50.0