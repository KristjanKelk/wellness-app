<!-- src/views/Dashboard.vue - Enhanced Version -->
<template>
  <div class="dashboard-page">
    <div class="dashboard">
      <div class="dashboard__header">
        <h1>Health Dashboard</h1>
        <p>Welcome back, {{ getUsernameDisplay() }}!</p>
        <div v-if="lastUpdated" class="last-updated">
          Last updated: {{ formatDateTime(lastUpdated) }}
        </div>
      </div>

      <div v-if="loading" class="dashboard__loading">
        <div class="loading-spinner"></div>
        <p>Loading your health data...</p>
      </div>

      <div v-else-if="error" class="dashboard__error">
        <div class="error-content">
          <div class="error-icon">⚠️</div>
          <p class="error-message">{{ error }}</p>
          <div class="error-actions">
            <button @click="fetchHealthData" class="btn btn-primary">
              Try Again
            </button>
            <router-link to="/profile" class="btn btn-secondary">
              Complete Profile
            </router-link>
          </div>
        </div>
      </div>

      <div v-else class="dashboard__content">
        <!-- New Milestones Notification -->
        <div v-if="newMilestones.length > 0" class="milestones-notification">
          <div class="notification-header">
            <h3>🎉 New Achievements!</h3>
            <button @click="dismissMilestones" class="dismiss-btn">&times;</button>
          </div>
          <div class="milestone-list">
            <div v-for="milestone in newMilestones" :key="milestone.id" class="milestone-item">
              <span class="milestone-icon">{{ getMilestoneIcon(milestone.milestone_type) }}</span>
              <span class="milestone-text">{{ milestone.description }}</span>
            </div>
          </div>
        </div>

        <!-- Wellness Score Card - Enhanced -->
        <wellness-score-card
          class="dashboard-card"
          :profile="profile"
          :score="formattedWellnessScore?.total || 0"
          :bmi-score="formattedWellnessScore?.components?.bmi?.score || 0"
          :activity-score="formattedWellnessScore?.components?.activity?.score || 0"
          :progress-score="formattedWellnessScore?.components?.progress?.score || 0"
          :habits-score="formattedWellnessScore?.components?.habits?.score || 0"
          :nutrition-score="formattedWellnessScore?.components?.nutrition?.score || 0"
          :score-breakdown="formattedWellnessScore?.breakdown"
          @recalculate="recalculateWellnessScore"
        />

        <!-- BMI Status Card -->
        <bmi-status-card
          class="dashboard-card"
          :bmi="bmi"
          :profile="profile"
        />

        <!-- Activity Level Card -->
        <activity-level-card
          class="dashboard-card"
          :profile="profile"
        />

        <!-- Activities Card -->
        <activities-card
          class="dashboard-card"
          :activities="activities"
          @activity-added="onActivityAdded"
        />

        <!-- Weight History Card -->
        <weight-history-card
          class="dashboard-card"
          :profile="profile"
          :weight-history="weightHistory"
          :weight-change="weightChange"
          @add-weight="showAddWeightModal = true"
          @weight-goal-achieved="onWeightGoalAchieved"
        />

        <!-- Meal Planning Card -->
        <meal-planning-card
          class="dashboard-card"
          :nutrition-profile="nutritionProfile"
          @navigate-to-meal-planning="navigateToMealPlanning"
        />

        <!-- AI Insights Card - Enhanced -->
        <ai-insights-card
          class="dashboard-card"
          :user-data="enhancedUserData"
          :loading="insightsLoading"
          @reload="regenerateInsights"
        />

        <!-- Milestones Card - Enhanced -->
        <milestones-card
          class="dashboard-card"
          :milestones="recentMilestones"
          :summary="milestoneSummary"
          @milestone-achieved="onMilestoneAchieved"
        />
      </div>

      <!-- Add Weight Modal -->
      <add-weight-modal
        v-if="showAddWeightModal"
        class="modal"
        :loading="weightLoading"
        :error="weightError"
        @close="showAddWeightModal = false"
        @save="saveNewWeight"
      />

      <!-- Milestone Achievement Modal -->
      <milestone-achievement-modal
        v-if="showMilestoneModal"
        :milestones="achievedMilestones"
        @close="closeMilestoneModal"
      />
    </div>
  </div>
</template>

<script>
import HealthProfileService from '../services/health-profile_service';
import AnalyticsService from '../services/analytics.service';
import WellnessService from '../services/wellness-service';
import ActivitiesService from '../services/activities.service';

// Import sub-components
import WellnessScoreCard from '../components/dashboard/WellnessScoreCard.vue';
import BmiStatusCard from '../components/dashboard/BmiStatusCard.vue';
import ActivityLevelCard from '../components/dashboard/ActivityLevelCard.vue';
import WeightHistoryCard from '../components/dashboard/WeightHistoryCard.vue';
import AiInsightsCard from '../components/dashboard/AiInsightsCard.vue';
import AddWeightModal from '../components/dashboard/AddWeightModal.vue';
import MilestonesCard from '../components/dashboard/MilestonesCard.vue';
import ActivitiesCard from '../components/dashboard/ActivitiesCard.vue';
import MealPlanningCard from '../components/dashboard/MealPlanningCard.vue';
import MilestoneAchievementModal from '../components/dashboard/MilestoneAchievementModal.vue';

export default {
  name: 'Dashboard',
  components: {
    WellnessScoreCard,
    BmiStatusCard,
    ActivityLevelCard,
    MealPlanningCard,
    WeightHistoryCard,
    AiInsightsCard,
    MilestonesCard,
    AddWeightModal,
    ActivitiesCard,
    MilestoneAchievementModal,

  },
  data() {
    return {
      profile: null,
      weightHistory: [],
      insights: [],
      insightsLoading: false,
      activities: [],
      recentMilestones: [],
      milestoneSummary: null,
      newMilestones: [],
      achievedMilestones: [],
      loading: true,
      error: null,
      bmi: null,
      rawWellnessScore: null,
      weightChange: null,
      lastUpdated: null,
      showAddWeightModal: false,
      showMilestoneModal: false,
      newWeight: null,
      weightLoading: false,
      weightError: null,
      nutritionProfile: null
    };
  },
  computed: {
    currentUser() {
      return this.$store.getters['auth/currentUser'];
    },
    hasProfileData() {
      return this.profile && this.profile.height_cm && this.profile.weight_kg;
    },
    formattedWellnessScore() {
      return AnalyticsService.formatWellnessScore(this.rawWellnessScore);
    },
    enhancedUserData() {
      return {
        ...this.profile,
        bmi: this.bmi,
        recentActivities: Array.isArray(this.activities) ? this.activities.length : 0,
        recentMilestones: Array.isArray(this.recentMilestones) ? this.recentMilestones.length : 0,
        restrictions: this.getUserRestrictions(),
        nutritionProfile: this.nutritionProfile,
        hasNutritionProfile: !!this.nutritionProfile
      };
    }
  },
  async mounted() {
    if (!this.currentUser) {
      this.$router.push('/login');
      return;
    }

    await this.initializeDashboard();
  },
  methods: {
    async initializeDashboard() {
      try {
        this.loading = true;
        this.error = null;

        // Fetch all dashboard data
        await this.fetchHealthData();

        if (this.hasProfileData) {
          await Promise.all([
            this.calculateBMI(),
            this.fetchAnalyticsData(),
            this.calculateWeightChange()
          ]);
        }

        this.lastUpdated = new Date();
      } catch (error) {
        console.error('Dashboard initialization error:', error);
        this.error = 'Failed to load your health data. Please try again.';
      } finally {
        this.loading = false;
      }
    },

    async fetchHealthData() {
  try {
    // Fetch profile, weight history, and nutrition profile
    const [profileResponse, weightResponse] = await Promise.all([
      HealthProfileService.getHealthProfile(),
      HealthProfileService.getWeightHistory()
    ]);

    // Fetch nutrition profile separately (might not exist yet)
    try {
      const { mealPlanningApi } = await import('@/services/mealPlanningApi');
      const nutritionResponse = await mealPlanningApi.getNutritionProfile();
      this.nutritionProfile = nutritionResponse.data;
    } catch (nutritionError) {
      console.warn('Nutrition profile not found:', nutritionError);
      this.nutritionProfile = null;
    }

    this.profile = profileResponse.data;

    // FIX: Handle paginated weight history response
    if (weightResponse.data && weightResponse.data.results) {
      this.weightHistory = weightResponse.data.results;
    } else if (Array.isArray(weightResponse.data)) {
      this.weightHistory = weightResponse.data;
    } else {
      this.weightHistory = [];
    }

    // Fetch recent activities
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = (() => {
      const d = new Date();
      d.setDate(d.getDate() - 14); // Last 2 weeks
      return d.toISOString().split('T')[0];
    })();

    try {
      const activitiesResponse = await ActivitiesService.getActivitiesByDateRange(startDate, endDate);
      // FIX: Handle paginated activities response
      if (activitiesResponse.data && activitiesResponse.data.results) {
        this.activities = activitiesResponse.data.results;
      } else if (Array.isArray(activitiesResponse.data)) {
        this.activities = activitiesResponse.data;
      } else {
        this.activities = [];
      }
    } catch (activityError) {
      console.error('Error fetching activities:', activityError);
      this.activities = []; // Fallback to empty array
    }

  } catch (error) {
    console.error('Error fetching health data:', error);
    if (error.response && error.response.status === 404) {
      this.error = 'Please complete your health profile to view your dashboard.';
    } else {
      this.error = 'Failed to load health data. Please try again.';
    }
    throw error;
  }
},

    async fetchAnalyticsData() {
      try {
        // Use the enhanced analytics service to get comprehensive data
        const analyticsData = await AnalyticsService.getDashboardAnalytics();

        this.rawWellnessScore = analyticsData.wellnessScore;
        this.recentMilestones = analyticsData.milestones;
        this.milestoneSummary = analyticsData.milestoneSummary;
        this.insights = analyticsData.insights;

        // If no wellness score exists, calculate one
        if (!this.rawWellnessScore && this.hasProfileData) {
          await this.recalculateWellnessScore();
        }

      } catch (error) {
        console.error('Error fetching analytics data:', error);
        // Don't throw error, continue with default values
      }
    },

    async recalculateWellnessScore() {
      try {
        const response = await AnalyticsService.calculateWellnessScore({
          weekly_activity_days: this.getWeeklyActivityDays()
        });

        this.rawWellnessScore = response.data;

        // Check for any new milestones achieved
        if (response.data.milestones_achieved && response.data.milestones_achieved.length > 0) {
          this.achievedMilestones = response.data.milestones_achieved;
          this.showMilestoneModal = true;

          // Refresh milestones data
          await this.fetchRecentMilestones();
        }

      } catch (error) {
        console.error('Error calculating wellness score:', error);
      }
    },

    async fetchRecentMilestones() {
      try {
        const response = await AnalyticsService.getRecentMilestones(30);

        // FIX: Extract the actual milestones array from the paginated response
        if (response.data && response.data.milestones) {
          // If response has milestones property
          this.recentMilestones = Array.isArray(response.data.milestones)
            ? response.data.milestones.filter(m => m !== null)
            : [];
        } else if (response.data && response.data.results) {
          // If paginated response
          this.recentMilestones = Array.isArray(response.data.results)
            ? response.data.results.filter(m => m !== null)
            : [];
        } else if (Array.isArray(response.data)) {
          // If direct array
          this.recentMilestones = response.data.filter(m => m !== null);
        } else {
          this.recentMilestones = [];
        }

      } catch (error) {
        console.error('Error fetching milestones:', error);
        this.recentMilestones = [];
      }
    },

    calculateBMI() {
      if (this.profile.height_cm && this.profile.weight_kg) {
        this.bmi = WellnessService.calculateBMI(this.profile.height_cm, this.profile.weight_kg);
      }
    },

    calculateWeightChange() {
      if (!this.weightHistory || this.weightHistory.length < 2) {
        this.weightChange = 0;
        return;
      }

      try {
        const sorted = [...this.weightHistory].sort((a, b) => new Date(b.recorded_at) - new Date(a.recorded_at));
        this.weightChange = sorted[0].weight_kg - sorted[1].weight_kg;
      } catch (e) {
        this.weightChange = 0;
      }
    },

    getWeeklyActivityDays() {
      // FIX: Ensure activities is an array before filtering
      if (!Array.isArray(this.activities)) {
        return 0;
      }

      try {
        // Calculate current week activity days from logged activities
        const now = new Date();
        const weekStart = new Date(now);
        weekStart.setDate(now.getDate() - now.getDay()); // Start of current week

        const thisWeekActivities = this.activities.filter(activity => {
          const activityDate = new Date(activity.performed_at);
          return activityDate >= weekStart;
        });

        // Count unique days
        const uniqueDays = new Set(
          thisWeekActivities.map(activity =>
            new Date(activity.performed_at).toDateString()
          )
        );

        return uniqueDays.size;
      } catch (error) {
        console.error('Error calculating weekly activity days:', error);
        return 0;
      }
    },

    getUserRestrictions() {
      if (!this.profile) return [];

      const restrictions = [];
      if (this.profile.is_gluten_free) restrictions.push('gluten_free');
      if (this.profile.is_dairy_free) restrictions.push('dairy_free');
      if (this.profile.is_nut_free) restrictions.push('nut_free');
      if (this.profile.has_other_restrictions && this.profile.other_restrictions_note) {
        restrictions.push(this.profile.other_restrictions_note);
      }

      return restrictions;
    },

    async saveNewWeight(weight) {
      if (!weight || weight < 20 || weight > 300) {
        this.weightError = 'Please enter a valid weight between 20 and 300 kg';
        return;
      }

      this.weightLoading = true;
      this.weightError = null;

      try {
        await HealthProfileService.addWeightEntry(weight);
        await HealthProfileService.updateHealthProfile({ ...this.profile, weight_kg: weight });

        // Refresh data and check for milestones
        await this.fetchHealthData();
        this.calculateBMI();
        this.calculateWeightChange();

        // Check for weight milestones
        const newMilestones = await AnalyticsService.checkForNewMilestones({
          weight_kg: weight
        });

        if (newMilestones.length > 0) {
          this.achievedMilestones = newMilestones;
          this.showMilestoneModal = true;
        }

        await this.recalculateWellnessScore();
        this.showAddWeightModal = false;

      } catch (error) {
        this.weightError = 'Failed to save weight. Please try again.';
      } finally {
        this.weightLoading = false;
      }
    },

    async onActivityAdded() {
      // Refresh activities and recalculate scores
      await this.fetchHealthData();
      await this.recalculateWellnessScore();
    },

    onWeightGoalAchieved() {
      // Handle weight goal achievement
      this.achievedMilestones.push({
        milestone_type: 'weight',
        description: `Congratulations! You've reached your weight goal of ${this.profile.target_weight_kg}kg!`
      });
      this.showMilestoneModal = true;
    },

    onMilestoneAchieved(milestone) {
      this.newMilestones.push(milestone);
      this.fetchRecentMilestones();
    },

    dismissMilestones() {
      this.newMilestones = [];
    },

    closeMilestoneModal() {
      this.showMilestoneModal = false;
      this.achievedMilestones = [];
    },

    getMilestoneIcon(type) {
      const icons = {
        weight: '⚖️',
        activity: '🏃',
        habit: '🔄'
      };
      return icons[type] || '🏆';
    },

    getUsernameDisplay() {
      if (this.currentUser) {
        if (this.currentUser.username) return this.currentUser.username;
        if (this.currentUser.access) {
          try {
            const base64Url = this.currentUser.access.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const json = decodeURIComponent(atob(base64).split('').map(c => '%'+('00'+c.charCodeAt(0).toString(16)).slice(-2)).join(''));
            const payload = JSON.parse(json);
            return payload.username || `User #${payload.user_id}`;
          } catch (e) {
            console.error("Error extracting username from token:", e);
          }
        }
      }
      return "User";
    },

    formatDateTime(date) {
      return new Date(date).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    async generateInsights() {
      if (!this.hasProfileData) return;

      this.insightsLoading = true;
      try {
        const response = await AnalyticsService.generateInsights(this.enhancedUserData);
        this.insights = response.data || [];
      } catch (error) {
        console.error('Error generating insights:', error);
        this.insights = [];
      } finally {
        this.insightsLoading = false;
      }
    },

    async regenerateInsights() {
      this.insightsLoading = true;
      try {
        await AnalyticsService.generateInsights(this.enhancedUserData, true);
        await this.fetchAnalyticsData();
      } catch (error) {
        console.error('Regeneration error:', error);
      } finally {
        this.insightsLoading = false;
      }
    },

    navigateToMealPlanning() {
      this.$router.push('/meal-planning');
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.dashboard-page {
  min-height: 100vh;
  background-color: $bg-light;
}

.dashboard__header {
  margin-bottom: $spacing-6;

  h1 {
    margin-bottom: $spacing-2;
  }

  .last-updated {
    font-size: $font-size-sm;
    color: $gray;
    margin-top: $spacing-2;
  }
}

.dashboard__loading,
.dashboard__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background-color: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
}

.dashboard__error {
  .error-content {
    text-align: center;

    .error-icon {
      font-size: 3rem;
      margin-bottom: $spacing-4;
    }

    .error-message {
      color: $error;
      margin-bottom: $spacing-6;
    }

    .error-actions {
      display: flex;
      gap: $spacing-3;
      justify-content: center;
    }
  }
}

.dashboard__content {
  display: grid;
  grid-template-columns: 1fr;
  gap: $spacing-6;

  @include responsive('md') {
    grid-template-columns: repeat(2, 1fr);
  }

  @include responsive('lg') {
    grid-template-columns: repeat(3, 1fr);
  }
}

.milestones-notification {
  grid-column: 1 / -1;
  background: linear-gradient(135deg, $success, lighten($success, 20%));
  color: $white;
  border-radius: $border-radius-lg;
  padding: $spacing-4;
  box-shadow: $shadow-lg;
  animation: slideDown 0.5s ease-out;

  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-3;

    h3 {
      margin: 0;
      font-size: $font-size-xl;
    }

    .dismiss-btn {
      background: none;
      border: none;
      color: $white;
      font-size: 1.5rem;
      cursor: pointer;
      padding: $spacing-1;
      border-radius: $border-radius;

      &:hover {
        background-color: rgba($white, 0.2);
      }
    }
  }

  .milestone-list {
    display: flex;
    flex-direction: column;
    gap: $spacing-2;
  }

  .milestone-item {
    display: flex;
    align-items: center;
    gap: $spacing-2;
    padding: $spacing-2;
    background-color: rgba($white, 0.1);
    border-radius: $border-radius;

    .milestone-icon {
      font-size: 1.2rem;
    }

    .milestone-text {
      font-weight: $font-weight-medium;
    }
  }
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid $gray-lighter;
  border-top-color: $primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: $spacing-4;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>