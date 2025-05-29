<!-- src/components/dashboard/AiInsightsCard.vue -->
<template>
  <dashboard-card title="AI Insights">
    <p v-if="statusMessage" class="status-message">{{ statusMessage }}</p>

    <!-- Loading State -->
    <template v-if="loading">
      <div class="dashboard-card__loading">
        <div class="loading-spinner"></div>
        <p>Loading your personalized AI insights...</p>
      </div>
    </template>

    <!-- Empty State -->
    <template v-else-if="!insights.length">
      <div class="dashboard-card__empty">
        <p>No insights available yet.</p>
        <button @click="reloadInsights(false)" class="refresh-button">
          Refresh Insights
        </button>
        <button @click="reloadInsights(true)" class="refresh-button">
          Generate New Insights
        </button>
      </div>
    </template>

    <!-- Insights Display -->
    <template v-else>
      <!-- Introductory Text (first item) -->
      <p v-if="intro" class="insights-intro">{{ intro }}</p>

      <!-- Detailed Insights List -->
      <div class="insights-container">
        <div
          v-for="insight in detailInsights"
          :key="insight.id"
          class="insight-item"
          :class="`priority-${insight.priority}`"
        >
          <div class="insight-header">
            <span class="priority-badge">
              {{ getPriorityDisplay(insight.priority) }}
            </span>
            <span class="insight-date">
              {{ formatDate(insight.created_at) }}
            </span>
          </div>
          <p class="insight-content">{{ insight.content }}</p>
        </div>
      </div>
      <div class="insights-actions">
        <button
          @click="reloadInsights(true)"
          class="action-btn primary"
          :disabled="loading"
        >
          Generate New Insights
        </button>
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
  props: {
    userData: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      insights: [],
      loading: false,
      error: null,
      statusMessage: ''
    };
  },
  created() {
    this.loadInsights(false);
  },
  computed: {
    // The first item is used as introductory text
    intro() {
      return this.insights[0]?.content || '';
    },
    detailInsights() {
      return this.insights.slice(1, 4);
    }
  },
  methods: {
    async loadInsights(force) {
      this.loading = true;
      this.error = null;
      this.statusMessage = '';
      try {
        const result = await AIInsightsService.generateInsights(this.userData, force);
        const all = Array.isArray(result.insights) ? result.insights : [];
        this.insights = all.slice(0, 4);

        if (force) {
          this.statusMessage = result.cached
            ? 'Showing cached insights – daily regeneration limit reached.'
            : 'Fresh AI insights generated!';
        }
      } catch (e) {
        if (e.response?.status === 429) {
          this.statusMessage = e.response.data.detail
            || 'You have reached the maximum regenerations for today.';
        } else {
          this.insights = [];
          this.error = e;
        }
      } finally {
        this.loading = false;
      }
    },
    reloadInsights(force = false) {
      this.loadInsights(force);
    },
    getPriorityDisplay(priority) {
      const map = { high: 'High', medium: 'Medium', low: 'Low' };
      return map[priority] || priority;
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

.status-message {
  margin-bottom: $spacing-4;
  font-weight: $font-weight-medium;
  color: $warning;
}

.insights-intro {
  margin-bottom: $spacing-4;
  font-weight: $font-weight-medium;
}

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

.insights-actions {
  margin-top: $spacing-4;
  display: flex;
  justify-content: center;
  align-items: center;
}

.action-btn.primary {
  padding: $spacing-3 $spacing-8;
  background-color: $primary;
  color: #fff;
  border: none;
  border-radius: $border-radius;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  &:hover { opacity: 0.9; }
}

.dashboard-card__empty {
  text-align: center;
  p { margin-bottom: $spacing-4; color: $gray; }
  .refresh-button {
    margin: 0 $spacing-2 $spacing-2 0;
  }
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
