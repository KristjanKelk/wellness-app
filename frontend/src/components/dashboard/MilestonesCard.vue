<!-- src/components/dashboard/MilestonesCard.vue -->
<template>
  <dashboard-card
    title="Achievements & Milestones"
    :isEmpty="!milestones || milestones.length === 0"
    :loading="loading"
  >
    <template v-slot:empty>
      <p>Complete your health profile and start tracking your progress to earn achievements!</p>
    </template>

    <div class="milestones-container">
      <div
        v-for="milestone in milestones"
        :key="milestone.id"
        class="milestone-item"
        :class="`milestone-${milestone.milestone_type}`"
      >
        <div class="milestone-icon">
          <span v-if="milestone.milestone_type === 'weight'">⚖️</span>
          <span v-else-if="milestone.milestone_type === 'activity'">🏃</span>
          <span v-else-if="milestone.milestone_type === 'habit'">🔄</span>
        </div>
        <div class="milestone-details">
          <h4 class="milestone-title">{{ milestone.description }}</h4>
          <span class="milestone-date">{{ formatDate(milestone.achieved_at) }}</span>
        </div>
      </div>

      <div class="milestone-footer">
        <p class="milestone-info">Milestones contribute to your wellness score!</p>
      </div>
    </div>
  </dashboard-card>
</template>

<script>
import DashboardCard from './DashboardCard.vue';
import AnalyticsService from '../../services/analytics.service';

export default {
  name: 'MilestonesCard',
  components: { DashboardCard },
  data() {
    return {
      milestones: [],
      loading: true,
      error: null,
    };
  },
  created() {
    this.loadMilestones();
  },
  methods: {
    async loadMilestones() {
      this.loading = true;
      try {
        const response = await AnalyticsService.getMilestones();
        this.milestones = response.data;
      } catch (error) {
        console.error('Failed to load milestones:', error);
        this.error = error;
      } finally {
        this.loading = false;
      }
    },
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';

.milestones-container {
  display: flex;
  flex-direction: column;
  gap: $spacing-4;
}

.milestone-item {
  display: flex;
  align-items: center;
  gap: $spacing-3;
  padding: $spacing-3;
  border-radius: $border-radius;
  background-color: #f9f9f9;

  &.milestone-weight {
    border-left: 4px solid #4caf50;
  }

  &.milestone-activity {
    border-left: 4px solid #2196f3;
  }

  &.milestone-habit {
    border-left: 4px solid #ff9800;
  }
}

.milestone-icon {
  font-size: 1.5rem;
  min-width: 32px;
  text-align: center;
}

.milestone-details {
  flex: 1;
}

.milestone-title {
  margin: 0 0 $spacing-1 0;
  font-size: $font-size-base;
}

.milestone-date {
  font-size: $font-size-sm;
  color: $gray;
}

.milestone-footer {
  margin-top: $spacing-4;
  text-align: center;
  font-style: italic;
  color: $gray;
  font-size: $font-size-sm;
}
</style>