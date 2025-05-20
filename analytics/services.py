# analytics/services.py
from decimal import Decimal
from django.utils import timezone
from .models import Milestone, WellnessScore
from health_profiles.models import HealthProfile, WeightHistory


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

    @staticmethod
    def check_habit_streak(user, habit_name, current_streak):
        """
        Check if user has achieved a habit streak milestone
        """
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

    @staticmethod
    def update_progress_score(user):
        """
        Update the wellness score based on milestone achievements
        """
        # Get the most recent wellness score
        try:
            profile = HealthProfile.objects.get(user=user)
            wellness_score = WellnessScore.objects.filter(health_profile=profile).order_by('-created_at').first()

            if not wellness_score:
                return None

            # Calculate milestones_achieved in the last 30 days
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
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


    @staticmethod
    def check_activity_milestone_by_count(user):
        """
        Check if user has achieved activity count milestones
        """
        try:
            profile = HealthProfile.objects.get(user=user)

            # Count total activities
            from health_profiles.models import Activity
            activity_count = Activity.objects.filter(health_profile=profile).count()

            # Activity count milestones
            count_milestones = [1, 5, 10, 25, 50, 100, 250, 500, 1000]

            for count in count_milestones:
                if activity_count == count:
                    # Check if this milestone already exists
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