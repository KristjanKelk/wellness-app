<!-- src/components/dashboard/AiInsightsCard.vue - Enhanced Version -->
<template>
  <dashboard-card title="AI Insights">
    <!-- Daily Limit Warning -->
    <div v-if="dailyLimitReached" class="daily-limit-warning">
      <div class="warning-icon">⚠️</div>
      <p>You've reached your daily AI insight generation limit. Showing cached insights.</p>
    </div>

    <!-- Status Message -->
    <p v-if="statusMessage" class="status-message" :class="statusMessageClass">
      {{ statusMessage }}
    </p>

    <!-- Loading State -->
    <template v-if="loading">
      <div class="dashboard-card__loading">
        <div class="loading-spinner"></div>
        <p>{{ loadingMessage }}</p>
      </div>
    </template>

    <!-- Empty State -->
    <template v-else-if="!insights.length">
      <div class="dashboard-card__empty">
        <div class="empty-icon">🤖</div>
        <p>No insights available yet.</p>
        <div class="empty-actions">
          <button @click="reloadInsights(false)" class="btn btn-primary" :disabled="loading">
            Generate Insights
          </button>
          <p class="help-text">Complete your health profile for personalized insights</p>
        </div>
      </div>
    </template>

    <!-- Insights Display -->
    <template v-else>
      <!-- Context Summary (if available) -->
      <div v-if="contextSummary" class="context-summary">
        <h4>Based on your profile:</h4>
        <div class="context-items">
          <span v-if="contextSummary.bmi" class="context-item">
            BMI: {{ contextSummary.bmi }}
          </span>
          <span v-if="contextSummary.recent_activities" class="context-item">
            {{ contextSummary.recent_activities }} recent activities
          </span>
          <span v-if="contextSummary.milestones_this_month" class="context-item">
            {{ contextSummary.milestones_this_month }} milestones this month
          </span>
        </div>
      </div>

      <!-- Insights List -->
      <div class="insights-container">
        <div
          v-for="(insight, index) in insights"
          :key="insight.id || index"
          class="insight-item"
          :class="`priority-${insight.priority}`"
        >
          <div class="insight-header">
            <span class="priority-badge" :class="`priority-${insight.priority}`">
              {{ getPriorityIcon(insight.priority) }}
              {{ getPriorityDisplay(insight.priority) }}
            </span>
            <span class="insight-date">
              {{ formatDate(insight.created_at) }}
            </span>
          </div>
          <p class="insight-content">{{ insight.content }}</p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="insights-actions">
        <button
          @click="reloadInsights(true)"
          class="btn btn-secondary"
          :disabled="loading || dailyLimitReached"
          :title="dailyLimitReached ? 'Daily regeneration limit reached' : 'Generate fresh insights (counts toward daily limit)'"
        >
          <svg v-if="loading" class="btn-spinner" width="16" height="16" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" opacity="0.3"/>
            <path d="M2 12C2 6.48 6.48 2 12 2" stroke="currentColor" stroke-width="2" fill="none"/>
          </svg>
          {{ loading ? 'Generating...' : 'Regenerate Insights' }}
        </button>

        <button
          @click="refreshCachedInsights"
          class="btn btn-text"
          :disabled="loading"
        >
          Refresh
        </button>
      </div>

      <!-- Generation Info -->
      <div class="generation-info">
        <div class="info-row">
          <span class="info-label">Last updated:</span>
          <span class="info-value">{{ formatDate(insights[0]?.created_at) }}</span>
        </div>
        <div v-if="cached" class="info-row">
          <span class="cached-indicator">📋 Showing cached insights</span>
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
      statusMessage: '',
      statusMessageClass: '',
      loadingMessage: 'Loading your personalized AI insights...',
      dailyLimitReached: false,
      cached: false,
      contextSummary: null
    };
  },
  created() {
    this.loadInsights(false);
  },
  methods: {
    async loadInsights(force = false) {
      this.loading = true;
      this.error = null;
      this.statusMessage = '';
      this.statusMessageClass = '';
      this.loadingMessage = force ? 'Generating fresh insights...' : 'Loading your personalized AI insights...';

      try {
        const result = await AIInsightsService.generateInsights(this.userData, force);

        // Handle different response structures
        if (result.insights) {
          this.insights = Array.isArray(result.insights) ? result.insights : [];
          this.cached = result.cached || false;
          this.contextSummary = result.context_summary || null;

          // Handle status messages
          if (force && result.cached) {
            this.statusMessage = 'Daily regeneration limit reached. Showing cached insights.';
            this.statusMessageClass = 'warning';
            this.dailyLimitReached = true;
          } else if (force && !result.cached) {
            this.statusMessage = 'Fresh insights generated successfully!';
            this.statusMessageClass = 'success';
            this.dailyLimitReached = false;
          }
        } else {
          // Fallback for direct insights array
          this.insights = Array.isArray(result) ? result : [];
        }

      } catch (error) {
        console.error('AI Insights error:', error);

        if (error.response?.status === 429) {
          // Rate limit exceeded
          this.statusMessage = error.response.data?.detail || 'Daily insight generation limit reached.';
          this.statusMessageClass = 'warning';
          this.dailyLimitReached = true;

          // Try to show any cached insights
          try {
            const cachedResult = await AIInsightsService.generateInsights(this.userData, false);
            if (cachedResult.insights) {
              this.insights = Array.isArray(cachedResult.insights) ? cachedResult.insights : [];
              this.cached = true;
            }
          } catch (cacheError) {
            console.error('Failed to load cached insights:', cacheError);
            this.insights = this.generateFallbackInsights();
          }
        } else {
          // Other errors - provide fallback insights
          this.insights = this.generateFallbackInsights();
          this.statusMessage = 'AI service temporarily unavailable. Showing general recommendations.';
          this.statusMessageClass = 'info';
        }
      } finally {
        this.loading = false;
      }
    },

    async reloadInsights(force = false) {
      await this.loadInsights(force);
    },

    async refreshCachedInsights() {
      await this.loadInsights(false);
    },

    generateFallbackInsights() {
      const fallbackInsights = [
        {
          content: "Stay hydrated by drinking at least 8 glasses of water daily for optimal health.",
          priority: "medium",
          created_at: new Date().toISOString()
        },
        {
          content: "Aim for 7-9 hours of quality sleep each night to support recovery and wellness.",
          priority: "high",
          created_at: new Date().toISOString()
        },
        {
          content: "Take a 10-minute walk after meals to improve digestion and blood sugar control.",
          priority: "low",
          created_at: new Date().toISOString()
        }
      ];

      // Customize based on available user data
      if (this.userData.fitness_goal === 'weight_loss') {
        fallbackInsights.unshift({
          content: "Focus on creating a moderate caloric deficit through both diet and exercise for sustainable weight loss.",
          priority: "high",
          created_at: new Date().toISOString()
        });
      }

      return fallbackInsights;
    },

    getPriorityDisplay(priority) {
      const map = {
        high: 'High Priority',
        medium: 'Medium Priority',
        low: 'Low Priority'
      };
      return map[priority] || priority;
    },

    getPriorityIcon(priority) {
      const icons = {
        high: '🔴',
        medium: '🟡',
        low: '🟢'
      };
      return icons[priority] || '🔵';
    },

    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.daily-limit-warning {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  padding: $spacing-3;
  background-color: rgba($warning, 0.1);
  border: 1px solid rgba($warning, 0.3);
  border-radius: $border-radius;
  margin-bottom: $spacing-4;

  .warning-icon {
    font-size: 1.2rem;
  }

  p {
    margin: 0;
    color: darken($warning, 20%);
    font-weight: $font-weight-medium;
  }
}

.status-message {
  margin-bottom: $spacing-4;
  padding: $spacing-2 $spacing-3;
  border-radius: $border-radius;
  font-weight: $font-weight-medium;

  &.success {
    background-color: rgba($success, 0.1);
    color: darken($success, 20%);
    border: 1px solid rgba($success, 0.3);
  }

  &.warning {
    background-color: rgba($warning, 0.1);
    color: darken($warning, 20%);
    border: 1px solid rgba($warning, 0.3);
  }

  &.info {
    background-color: rgba($info, 0.1);
    color: darken($info, 20%);
    border: 1px solid rgba($info, 0.3);
  }
}

.context-summary {
  margin-bottom: $spacing-4;
  padding: $spacing-3;
  background-color: $bg-light;
  border-radius: $border-radius;

  h4 {
    margin: 0 0 $spacing-2 0;
    font-size: $font-size-sm;
    color: $gray;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .context-items {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-2;
  }

  .context-item {
    padding: $spacing-1 $spacing-2;
    background-color: $white;
    border-radius: $border-radius-sm;
    font-size: $font-size-sm;
    color: $secondary;
  }
}

.insights-container {
  display: flex;
  flex-direction: column;
  gap: $spacing-3;
  margin-bottom: $spacing-4;
}

.insight-item {
  border-left: 4px solid $gray-lighter;
  padding: $spacing-3;
  background-color: #f9f9f9;
  border-radius: 0 $border-radius $border-radius 0;

  &.priority-high {
    border-left-color: $error;
    background-color: rgba($error, 0.03);
  }
  &.priority-medium {
    border-left-color: $warning;
    background-color: rgba($warning, 0.03);
  }
  &.priority-low {
    border-left-color: $success;
    background-color: rgba($success, 0.03);
  }

  .insight-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-2;
    font-size: $font-size-sm;

    .priority-badge {
      display: flex;
      align-items: center;
      gap: $spacing-1;
      font-weight: $font-weight-medium;

      &.priority-high { color: $error; }
      &.priority-medium { color: $warning; }
      &.priority-low { color: $success; }
    }

    .insight-date {
      color: $gray;
    }
  }

  .insight-content {
    line-height: 1.5;
    margin: 0;
  }
}

.insights-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-4;
  gap: $spacing-3;
}

.generation-info {
  padding-top: $spacing-3;
  border-top: 1px solid $gray-lighter;
  font-size: $font-size-sm;

  .info-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: $spacing-1;
  }

  .info-label {
    color: $gray;
  }

  .info-value {
    color: $secondary;
    font-weight: $font-weight-medium;
  }

  .cached-indicator {
    color: $info;
    font-style: italic;
  }
}

.dashboard-card__empty {
  text-align: center;
  padding: $spacing-6;

  .empty-icon {
    font-size: 3rem;
    margin-bottom: $spacing-4;
  }

  .empty-actions {
    margin-top: $spacing-4;
  }

  .help-text {
    margin-top: $spacing-2;
    color: $gray;
    font-size: $font-size-sm;
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

.btn-spinner {
  animation: spin 1s linear infinite;
  margin-right: $spacing-1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>