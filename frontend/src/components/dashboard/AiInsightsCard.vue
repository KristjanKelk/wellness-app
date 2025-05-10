<!-- src/components/dashboard/AiInsightsCard.vue -->
<template>
  <dashboard-card
    title="AI Insights"
    :isEmpty="!insights || insights.length === 0"
  >
    <template v-slot:empty>
      <p>Personalized health insights will appear here once your profile is complete.</p>
      <p class="insights-info">Our AI analyzes your health data to provide actionable recommendations.</p>
    </template>

    <div class="insights-container">
      <div v-for="(insight, index) in insights" :key="index"
           class="insight-item" :class="'priority-'+insight.priority">
        <div class="insight-header">
          <span class="priority-badge">{{ getPriorityDisplay(insight.priority) }}</span>
          <span class="insight-date">{{ formatDate(insight.created_at) }}</span>
        </div>
        <p class="insight-content">{{ insight.content }}</p>
      </div>
    </div>
  </dashboard-card>
</template>

<script>
import DashboardCard from './DashboardCard.vue';
import WellnessService from '../../services/wellness-service';

export default {
  name: 'AiInsightsCard',
  components: {
    DashboardCard
  },
  props: {
    insights: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    getPriorityDisplay(priority) {
      return WellnessService.getPriorityDisplay(priority);
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
@import '@/assets/styles/_utilities.scss';

.insights-container {
  display: flex;
  flex-direction: column;
}

.insight-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: $spacing-2;
  font-size: 0.85rem;
}

.priority-badge {
  font-weight: $font-weight-semibold;
}

.insight-date {
  color: $gray;
}

.insight-content {
  line-height: 1.5;
  margin: 0;
}

.insights-info {
  color: $gray;
  font-style: italic;
  margin-top: $spacing-2;
}

// Override insight-item styles for specific priorities
.priority-high .priority-badge {
  color: $error;
}

.priority-medium .priority-badge {
  color: $warning;
}

.priority-low .priority-badge {
  color: $info;
}
</style>