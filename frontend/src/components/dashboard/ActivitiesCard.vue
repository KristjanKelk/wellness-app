<!-- src/components/dashboard/ActivitiesCard.vue -->
<template>
  <dashboard-card
    title="Activities"
    :loading="loading"
    :error="error"
  >
    <div class="activities-container">
      <!-- Quick Stats Section -->
      <div class="activities-stats">
        <div class="stats-header">
          <h3>Activity Summary</h3>
          <div class="time-period-selector">
            <button
              v-for="period in timePeriods"
              :key="period.value"
              @click="selectedPeriod = period.value"
              :class="{ active: selectedPeriod === period.value }"
              class="period-btn"
            >
              {{ period.label }}
            </button>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7V17C2 19.21 3.79 21 6 21H18C20.21 21 22 19.21 22 17V7L12 2Z" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 12L2 7" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 12L22 7" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 12V22" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ periodStats.totalActivities }}</div>
              <div class="stat-label">Activities</div>
            </div>
          </div>

          <div class="stat-item">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="#30C1B1" stroke-width="2"/>
                <path d="M12 6V12L16 14" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatDuration(periodStats.totalDuration) }}</div>
              <div class="stat-label">Total Time</div>
            </div>
          </div>

          <div class="stat-item">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 6L9 17L4 12" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ periodStats.activeDays }}</div>
              <div class="stat-label">Active Days</div>
            </div>
          </div>

          <div class="stat-item" v-if="periodStats.totalDistance > 0">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M13 16H12V12H11M12 8H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ periodStats.totalDistance.toFixed(1) }}</div>
              <div class="stat-label">Distance (km)</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Activity Type Distribution -->
      <div class="activity-distribution" v-if="activityDistribution.length > 0">
        <h3>Activity Breakdown</h3>
        <div class="distribution-chart">
          <div
            v-for="(activity, index) in activityDistribution"
            :key="index"
            class="distribution-bar"
            :style="{ width: activity.percentage + '%' }"
            :class="`type-${activity.type}`"
            :title="`${activity.label}: ${activity.count} activities`"
          >
            <span v-if="activity.percentage > 10">{{ activity.count }}</span>
          </div>
        </div>
        <div class="distribution-legend">
          <div
            v-for="(activity, index) in activityDistribution"
            :key="index"
            class="legend-item"
          >
            <span class="legend-color" :class="`type-${activity.type}`"></span>
            <span class="legend-label">{{ activity.label }} ({{ activity.count }})</span>
          </div>
        </div>
      </div>

      <!-- Recent Activities -->
      <div class="recent-activities" v-if="recentActivities.length > 0">
        <h3>Recent Activities</h3>
        <div class="activity-list">
          <div
            v-for="activity in recentActivities"
            :key="activity.id"
            class="activity-item"
          >
            <div :class="`activity-icon type-${activity.activity_type}`">
              <span>{{ getActivityIcon(activity.activity_type) }}</span>
            </div>
            <div class="activity-details">
              <div class="activity-name">{{ activity.name }}</div>
              <div class="activity-meta">
                <span>{{ formatDate(activity.performed_at) }}</span>
                <span>{{ activity.duration_minutes }} min</span>
                <span v-if="activity.distance_km">{{ activity.distance_km }} km</span>
                <span v-if="activity.calories_burned">{{ activity.calories_burned }} cal</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Add Activity Button -->
      <button @click="showAddActivityModal = true" class="btn btn-primary btn-block">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Log New Activity
      </button>

      <!-- View More Link -->
      <div class="view-all-link" v-if="recentActivities.length >= 5">
        <router-link to="/activities">View all activities</router-link>
      </div>
    </div>

    <!-- Add Activity Modal -->
    <add-activity-modal
      v-if="showAddActivityModal"
      :loading="modalLoading"
      :error="modalError"
      @close="showAddActivityModal = false"
      @save="saveNewActivity"
    />
  </dashboard-card>
</template>

<script>
import DashboardCard from './DashboardCard.vue';
import AddActivityModal from './AddActivityModal.vue';
import ActivitiesService from '../../services/activities.service';

export default {
  name: 'ActivitiesCard',
  components: {
    DashboardCard,
    AddActivityModal
  },
  data() {
    return {
      loading: false,
      error: null,
      selectedPeriod: 'week',
      timePeriods: [
        { value: 'week', label: 'Week' },
        { value: 'month', label: 'Month' },
        { value: 'year', label: 'Year' }
      ],
      activities: [],
      recentActivities: [],
      showAddActivityModal: false,
      modalLoading: false,
      modalError: null
    };
  },
  computed: {
    periodStats() {
      const now = new Date();
      let startDate = new Date();

      // Calculate start date based on selected period
      switch (this.selectedPeriod) {
        case 'week':
          startDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          startDate.setMonth(now.getMonth() - 1);
          break;
        case 'year':
          startDate.setFullYear(now.getFullYear() - 1);
          break;
      }

      // Filter activities within the period
      const periodActivities = this.activities.filter(activity => {
        const activityDate = new Date(activity.performed_at);
        return activityDate >= startDate;
      });

      // Calculate statistics
      const totalActivities = periodActivities.length;
      const totalDuration = periodActivities.reduce((sum, activity) => sum + (activity.duration_minutes || 0), 0);
      const totalDistance = periodActivities.reduce((sum, activity) => sum + (parseFloat(activity.distance_km) || 0), 0);

      // Calculate active days
      const uniqueDays = new Set(
        periodActivities.map(activity =>
          new Date(activity.performed_at).toLocaleDateString()
        )
      );
      const activeDays = uniqueDays.size;

      return {
        totalActivities,
        totalDuration,
        totalDistance,
        activeDays
      };
    },
    activityDistribution() {
      const distribution = {};
      const periodActivities = this.getActivitiesForPeriod();

      // Count activities by type
      periodActivities.forEach(activity => {
        if (!distribution[activity.activity_type]) {
          distribution[activity.activity_type] = 0;
        }
        distribution[activity.activity_type]++;
      });

      // Convert to array and calculate percentages
      const total = periodActivities.length;
      return Object.entries(distribution).map(([type, count]) => ({
        type,
        label: this.getActivityTypeLabel(type),
        count,
        percentage: total > 0 ? (count / total) * 100 : 0
      })).sort((a, b) => b.count - a.count);
    }
  },
  mounted() {
    this.fetchActivities();
  },
  methods: {
    async fetchActivities() {
      this.loading = true;
      this.error = null;

      try {
        const response = await ActivitiesService.getAllActivities();
        this.activities = response.data;

        // Get recent activities (last 5)
        this.recentActivities = [...this.activities]
          .sort((a, b) => new Date(b.performed_at) - new Date(a.performed_at))
          .slice(0, 5);
      } catch (error) {
        console.error('Failed to fetch activities:', error);
        this.error = 'Failed to load activities. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    getActivitiesForPeriod() {
      const now = new Date();
      let startDate = new Date();

      switch (this.selectedPeriod) {
        case 'week':
          startDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          startDate.setMonth(now.getMonth() - 1);
          break;
        case 'year':
          startDate.setFullYear(now.getFullYear() - 1);
          break;
      }

      return this.activities.filter(activity => {
        const activityDate = new Date(activity.performed_at);
        return activityDate >= startDate;
      });
    },
    async saveNewActivity(activityData) {
      this.modalLoading = true;
      this.modalError = null;

      try {
        await ActivitiesService.createActivity(activityData);
        await this.fetchActivities();
        this.showAddActivityModal = false;
      } catch (error) {
        console.error('Failed to save activity:', error);
        this.modalError = 'Failed to save activity. Please try again.';
      } finally {
        this.modalLoading = false;
      }
    },
    formatDuration(minutes) {
      if (minutes < 60) {
        return `${minutes}m`;
      }
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    },
    formatDate(dateString) {
      const date = new Date(dateString);
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);

      if (date.toDateString() === today.toDateString()) {
        return 'Today';
      } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
      } else {
        return date.toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric'
        });
      }
    },
    getActivityIcon(type) {
      const icons = {
        cardio: '🏃',
        strength: '💪',
        flexibility: '🧘',
        sports: '⚽',
        hiit: '⚡',
        yoga: '🧘',
        other: '🏋️'
      };
      return icons[type] || '🏃';
    },
    getActivityTypeLabel(type) {
      const labels = {
        cardio: 'Cardio',
        strength: 'Strength',
        flexibility: 'Flexibility',
        sports: 'Sports',
        hiit: 'HIIT',
        yoga: 'Yoga',
        other: 'Other'
      };
      return labels[type] || type;
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';

.activities-container {
  padding: $spacing-4 0;
}

.activities-stats {
  margin-bottom: $spacing-6;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-4;
  flex-wrap: wrap;
  gap: $spacing-3;

  h3 {
    margin: 0;
    font-size: $font-size-lg;
  }
}

.time-period-selector {
  display: flex;
  gap: $spacing-1;
  background-color: $gray-lighter;
  border-radius: $border-radius;
  padding: 2px;
}

.period-btn {
  padding: $spacing-2 $spacing-3;
  border: none;
  background: transparent;
  color: $gray-dark;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  border-radius: $border-radius-sm;
  cursor: pointer;
  transition: $transition-base;

  &.active {
    background-color: $white;
    color: $primary;
    box-shadow: $shadow-sm;
  }

  &:hover:not(.active) {
    color: $secondary;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: $spacing-4;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: $spacing-3;
  padding: $spacing-3;
  background-color: $bg-light;
  border-radius: $border-radius;
}

.stat-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba($primary, 0.1);
  border-radius: $border-radius;
  flex-shrink: 0;
}

.stat-info {
  .stat-value {
    font-size: $font-size-xl;
    font-weight: $font-weight-bold;
    color: $secondary;
  }

  .stat-label {
    font-size: $font-size-sm;
    color: $gray;
  }
}

.activity-distribution {
  margin-bottom: $spacing-6;

  h3 {
    margin-bottom: $spacing-3;
    font-size: $font-size-lg;
  }
}

.distribution-chart {
  display: flex;
  height: 30px;
  background-color: $gray-lighter;
  border-radius: $border-radius;
  overflow: hidden;
  margin-bottom: $spacing-3;
}

.distribution-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  color: $white;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  transition: $transition-base;

  &.type-cardio { background-color: #FF6B6B; }
  &.type-strength { background-color: #4ECDC4; }
  &.type-flexibility { background-color: #45B7D1; }
  &.type-sports { background-color: #96CEB4; }
  &.type-hiit { background-color: #FECA57; }
  &.type-yoga { background-color: #DDA0DD; }
  &.type-other { background-color: #95A5A6; }
}

.distribution-legend {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-3;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  font-size: $font-size-sm;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: $border-radius-sm;

  &.type-cardio { background-color: #FF6B6B; }
  &.type-strength { background-color: #4ECDC4; }
  &.type-flexibility { background-color: #45B7D1; }
  &.type-sports { background-color: #96CEB4; }
  &.type-hiit { background-color: #FECA57; }
  &.type-yoga { background-color: #DDA0DD; }
  &.type-other { background-color: #95A5A6; }
}

.recent-activities {
  margin-bottom: $spacing-6;

  h3 {
    margin-bottom: $spacing-3;
    font-size: $font-size-lg;
  }
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-3;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: $spacing-3;
  padding: $spacing-3;
  background-color: $bg-light;
  border-radius: $border-radius;
  transition: $transition-base;

  &:hover {
    background-color: darken($bg-light, 3%);
  }
}

.activity-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $border-radius;
  font-size: 1.2rem;

  &.type-cardio { background-color: rgba(#FF6B6B, 0.2); }
  &.type-strength { background-color: rgba(#4ECDC4, 0.2); }
  &.type-flexibility { background-color: rgba(#45B7D1, 0.2); }
  &.type-sports { background-color: rgba(#96CEB4, 0.2); }
  &.type-hiit { background-color: rgba(#FECA57, 0.2); }
  &.type-yoga { background-color: rgba(#DDA0DD, 0.2); }
  &.type-other { background-color: rgba(#95A5A6, 0.2); }
}

.activity-details {
  flex: 1;

  .activity-name {
    font-weight: $font-weight-medium;
    color: $secondary;
    margin-bottom: $spacing-1;
  }

  .activity-meta {
    display: flex;
    gap: $spacing-3;
    font-size: $font-size-sm;
    color: $gray;

    span {
      position: relative;

      &:not(:last-child)::after {
        content: '•';
        position: absolute;
        right: -($spacing-3 / 2);
        color: $gray-light;
      }
    }
  }
}

.btn-block {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-2;
  margin-bottom: $spacing-4;
}

.view-all-link {
  text-align: center;
  margin-top: $spacing-4;
}
</style>