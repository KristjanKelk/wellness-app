<template>
  <div class="card">
    <h2>AI Insights</h2>
    <div v-if="insights && insights.length > 0" class="insights-container">
      <div v-for="(insight, index) in insights" :key="index"
           class="insight-item" :class="'priority-'+insight.priority">
        <div class="insight-header">
          <span class="priority-badge">{{ getPriorityDisplay(insight.priority) }}</span>
          <span class="insight-date">{{ formatDate(insight.created_at) }}</span>
        </div>
        <p class="insight-content">{{ insight.content }}</p>
      </div>
    </div>
    <div v-else>
      <p>Personalized health insights will appear here once your profile is complete.</p>
      <p class="insights-info">Our AI analyzes your health data to provide actionable recommendations.</p>
    </div>
  </div>
</template>

<script>
import WellnessService from '../../services/wellness-service';

export default {
  name: 'AiInsightsCard',
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