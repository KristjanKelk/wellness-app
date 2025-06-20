<!-- src/components/dashboard/MilestonesCard.vue -->
<template>
  <dashboard-card
    title="Achievements & Milestones"
    :isEmpty="!filteredMilestones || filteredMilestones.length === 0"
    :loading="loading"
  >
    <template v-slot:empty>
      <p>Complete your health profile and start tracking your progress to earn achievements!</p>
    </template>

    <div class="milestones-container">
      <div
        v-for="milestone in filteredMilestones"
        :key="milestone.id"
        class="milestone-item"
        :class="`milestone-${milestone.milestone_type}`"
      >
        <div class="milestone-icon">
          <span v-if="milestone.milestone_type === 'weight'">⚖️</span>
          <span v-else-if="milestone.milestone_type === 'activity'">🏃</span>
          <span v-else-if="milestone.milestone_type === 'habit'">🔄</span>
          <span v-else>🏆</span>
        </div>
        <div class="milestone-details">
          <h4 class="milestone-title">{{ milestone.description || 'Achievement unlocked!' }}</h4>
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
  props: {
    // Accept milestones as props from parent (Dashboard)
    milestones: {
      type: [Array, Object], // Allow both Array and Object to handle different response formats
      default: () => []
    },
    summary: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      localMilestones: [],
      loading: false,
      error: null,
    };
  },
  computed: {
    // FIX: Handle both prop milestones and extract from object if needed
    filteredMilestones() {
      let milestones = [];

      // First, try to get milestones from props
      if (this.milestones) {
        if (Array.isArray(this.milestones)) {
          // If it's already an array
          milestones = this.milestones;
        } else if (this.milestones.milestones && Array.isArray(this.milestones.milestones)) {
          // If it's a paginated object with milestones property
          milestones = this.milestones.milestones;
        } else if (this.milestones.results && Array.isArray(this.milestones.results)) {
          // If it's a paginated object with results property
          milestones = this.milestones.results;
        }
      }

      // Fallback to local milestones if prop milestones are empty
      if (milestones.length === 0 && Array.isArray(this.localMilestones)) {
        milestones = this.localMilestones;
      }

      // Filter out null/undefined milestones
      return milestones.filter(milestone =>
        milestone !== null &&
        milestone !== undefined &&
        milestone.id &&
        milestone.description
      );
    }
  },
  created() {
    // Only load milestones if not provided via props
    if (!this.milestones || (Array.isArray(this.milestones) && this.milestones.length === 0)) {
      this.loadMilestones();
    }
  },
  methods: {
    async loadMilestones() {
      this.loading = true;
      try {
        const response = await AnalyticsService.getMilestones();

        // Handle paginated response
        if (response.data && response.data.results) {
          this.localMilestones = response.data.results.filter(m => m !== null);
        } else if (Array.isArray(response.data)) {
          this.localMilestones = response.data.filter(m => m !== null);
        } else {
          this.localMilestones = [];
        }
      } catch (error) {
        console.error('Failed to load milestones:', error);
        this.error = error;
        this.localMilestones = [];
      } finally {
        this.loading = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'Date unknown';
      try {
        const date = new Date(dateString);
        return date.toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
      } catch (error) {
        console.error('Error formatting date:', dateString, error);
        return 'Invalid date';
      }
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