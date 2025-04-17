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