<!-- src/components/dashboard/AiInsightsCard.vue -->
<template>
  <dashboard-card title="AI Insights">
    <template v-if="loading">
      <div class="dashboard-card__loading">
        <div class="loading-spinner"></div>
        <p>Loading your personalized AI insights...</p>
      </div>
    </template>

    <template v-else-if="!insights.length">
      <div class="dashboard-card__empty">
        <p>No insights available yet.</p>
        <button @click="reloadInsights" class="refresh-button">Refresh Insights</button>
      </div>
    </template>

    <template v-else>
      <div class="insights-container">
        <div
          v-for="insight in insights"
          :key="insight.id"
          class="insight-item"
          :class="`priority-${insight.priority}`"
        >
          <div class="insight-header">
            <span class="priority-badge">{{ getPriorityDisplay(insight.priority) }}</span>
            <span class="insight-date">{{ formatDate(insight.created_at) }}</span>
          </div>
          <p class="insight-content">{{ insight.content }}</p>
        </div>
      </div>
    </template>
  </dashboard-card>
</template>

<script>
import DashboardCard from './DashboardCard.vue';
import AIInsightsService from '../../services/ai-insights.service';

export default {
  name: 'AiInsightsCard',
  components: { DashboardCard },
  data() {
    return {
      insights: [],
      loading: false,
      error: null,
    };
  },
  created() {
    this.loadInsights();
  },
  methods: {
    async loadInsights() {
      this.loading = true;
      try {
        this.insights = await AIInsightsService.generateInsights();
      } catch (e) {
        console.error('Failed to load insights:', e);
        this.error = e;
      } finally {
        this.loading = false;
      }
    },
    reloadInsights() {
      this.loadInsights();
    },
    getPriorityDisplay(priority) {
      const map = { high: 'High', medium: 'Medium', low: 'Low' };
      return map[priority] || priority;
    },
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    },
  },
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.insights-container {
  display: flex;
  flex-direction: column;
  gap: $spacing-4;
}

.insight-item {
  border-left: 4px solid $gray-lighter;
  padding: $spacing-3 $spacing-4;
  background-color: #f9f9f9;
  border-radius: 0 $border-radius $border-radius 0;

  &.priority-high { border-left-color: $error; }
  &.priority-medium { border-left-color: $warning; }
  &.priority-low { border-left-color: $info; }

  .insight-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: $spacing-2;
    font-size: $font-size-sm;

    .priority-badge { font-weight: $font-weight-bold; }
    .insight-date    { color: $gray; }
  }

  .insight-content { line-height: 1.5; }
}

.dashboard-card__empty {
  text-align: center;
  p { margin-bottom: $spacing-4; color: $gray; }
}

.dashboard-card__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-6;

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid $gray-lighter;
    border-top-color: $primary;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: $spacing-4;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.refresh-button {
  padding: $spacing-2 $spacing-4;
  background-color: $primary;
  color: #fff;
  border: none;
  border-radius: $border-radius;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  &:hover { opacity: 0.9; }
}
</style>