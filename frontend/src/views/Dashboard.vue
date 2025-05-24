<template>
  <div class="dashboard-page">
    <div class="dashboard">
      <div class="dashboard__header">
        <h1>Health Dashboard</h1>
        <p>Welcome, {{ getUsernameDisplay() }}!</p>
      </div>

      <div v-if="loading" class="dashboard__loading">
        <div class="loading-spinner"></div>
        <p>Loading your health data...</p>
      </div>

      <div v-else-if="error" class="dashboard__error">
        <p class="error-message">{{ error }}</p>
        <router-link to="/profile" class="btn btn-primary">Complete Your Profile</router-link>
      </div>

      <div v-else class="dashboard__content">
        <!-- Wellness Score Card -->
        <wellness-score-card
            class="dashboard-card"
            :profile="profile"
            :score="wellnessScore"
            :bmi-score="bmiScore"
            :activity-score="activityScore"
            :progress-score="progressScore"
            :habits-score="habitsScore"
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
        />

        <!-- Weight History Card -->
        <weight-history-card
            class="dashboard-card"
            :profile="profile"
            :weight-history="weightHistory"
            :weight-change="weightChange"
            @add-weight="showAddWeightModal = true"
        />

        <!-- AI Insights Card -->
        <ai-insights-card
            class="dashboard-card"
            :insights="insights"
        />

        <!-- Milestones Card -->
        <milestones-card
            class="dashboard-card"
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
    </div>
  </div>
</template>

<script>
import HealthProfileService from '../services/health-profile_service';
import WellnessService from '../services/wellness-service';
import AIInsightsService from '../services/ai-insights.service';


// Import sub-components
import WellnessScoreCard from '../components/dashboard/WellnessScoreCard.vue';
import BmiStatusCard from '../components/dashboard/BmiStatusCard.vue';
import ActivityLevelCard from '../components/dashboard/ActivityLevelCard.vue';
import WeightHistoryCard from '../components/dashboard/WeightHistoryCard.vue';
import AiInsightsCard from '../components/dashboard/AiInsightsCard.vue';
import AddWeightModal from '../components/dashboard/AddWeightModal.vue';
import MilestonesCard from '../components/dashboard/MilestonesCard.vue';
import ActivitiesCard from '../components/dashboard/ActivitiesCard.vue';

export default {
  name: 'Dashboard',
  components: {
    WellnessScoreCard,
    BmiStatusCard,
    ActivityLevelCard,
    WeightHistoryCard,
    AiInsightsCard,
    MilestonesCard,
    AddWeightModal,
    ActivitiesCard
  },
  data() {
    return {
      profile: null,
      weightHistory: [],
      insights: [],
      loading: true,
      error: null,
      bmi: null,
      wellnessScore: 0,
      bmiScore: 0,
      activityScore: 0,
      progressScore: 0,
      habitsScore: 0,
      weightChange: null,
      showAddWeightModal: false,
      newWeight: null,
      weightLoading: false,
      weightError: null
    };
  },
  computed: {
    currentUser() {
      return this.$store.getters['auth/currentUser'];
    },
    hasProfileData() {
      return this.profile && this.profile.height_cm && this.profile.weight_kg;
    }
  },
  async mounted() {
    if (!this.currentUser) {
      this.$router.push('/login');
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 100));

    try {
      await this.fetchHealthData();
      if (this.hasProfileData) {
        this.calculateBMI();
        this.calculateWellnessScore();
        if (this.weightHistory && this.weightHistory.length > 0) {
          this.calculateWeightChange();
        }
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      this.error = 'Failed to load your health data. Please try again.';
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async fetchHealthData() {
      try {
        const profileResponse = await HealthProfileService.getHealthProfile();
        this.profile = profileResponse.data;

        const weightResponse = await HealthProfileService.getWeightHistory();
        this.weightHistory = weightResponse.data;

        if (this.profile) {
          try {
            const userData = {
              ...this.profile,
              bmi: this.bmi
            };

            const insightsResponse = await AIInsightsService.generateInsights(userData);
            this.insights = insightsResponse.data;
          } catch (insightError) {
            console.error('Error generating insights:', insightError);
            this.insights = [{
              content: "Complete your health profile to receive personalized insights.",
              priority: "medium",
              created_at: new Date()
            }];
          }
        }
      } catch (error) {
        console.error('Error fetching health data:', error);
        if (error.response && error.response.status === 404) {
          this.error = 'Please complete your health profile to view your dashboard.';
        } else {
          throw error;
        }
      }
    },
    calculateBMI() {
      if (this.profile.height_cm && this.profile.weight_kg) {
        this.bmi = WellnessService.calculateBMI(this.profile.height_cm, this.profile.weight_kg);
      }
    },
    calculateWellnessScore() {
      if (this.bmi) {
        this.bmiScore = WellnessService.calculateBMIScore(this.bmi);
      }

      this.activityScore = WellnessService.calculateActivityScore(this.profile.activity_level);
      this.progressScore = 60;
      this.habitsScore = 50;
      this.wellnessScore = WellnessService.calculateWellnessScore(
          this.bmiScore,
          this.activityScore,
          this.progressScore,
          this.habitsScore
      );
    },
    calculateWeightChange() {
      if (!this.weightHistory || this.weightHistory.length < 2) {
        this.weightChange = 0;
        return;
      }

      try {
        const sortedHistory = [...this.weightHistory].sort((a, b) =>
            new Date(b.recorded_at) - new Date(a.recorded_at)
        );

        if (sortedHistory.length >= 2) {
          const latest = sortedHistory[0];
          const previous = sortedHistory[1];

          this.weightChange = latest.weight_kg - previous.weight_kg;
        } else {
          this.weightChange = 0;
        }
      } catch (error) {
        console.error('Error calculating weight change:', error);
        this.weightChange = 0;
      }
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
        const profileData = { ...this.profile, weight_kg: weight };
        await HealthProfileService.updateHealthProfile(profileData);
        await this.fetchHealthData();
        this.calculateBMI();
        this.calculateWellnessScore();

        if (this.weightHistory && this.weightHistory.length > 0) {
          this.calculateWeightChange();
        }
        this.showAddWeightModal = false;
      } catch (error) {
        this.weightError = 'Failed to save weight. Please try again.';
      } finally {
        this.weightLoading = false;
      }
    },
    getUsernameDisplay() {
      if (this.currentUser) {
        if (this.currentUser.username) {
          return this.currentUser.username;
        }
        if (this.currentUser.access) {
          try {
            const base64Url = this.currentUser.access.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
              return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));

            const payload = JSON.parse(jsonPayload);
            if (payload.username) return payload.username;
            if (payload.user_id) return `User #${payload.user_id}`;
          } catch (e) {
            console.error("Error extracting username from token:", e);
          }
        }
      }
      return "User";
    }
  }
};
</script>

<style lang="scss" scoped>
</style>