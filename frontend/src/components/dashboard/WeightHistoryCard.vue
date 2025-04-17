<!-- src/components/dashboard/WeightHistoryCard.vue -->
<template>
  <dashboard-card
    title="Weight History"
    :isEmpty="!weightHistory || weightHistory.length === 0"
    :error="error"
  >
    <template v-slot:empty>
      <p>Your weight history will appear once you start tracking your weight.</p>
      <button @click="$emit('add-weight')" class="btn btn-primary">
        Start Tracking Weight
      </button>
    </template>

    <div class="weight-container">
      <div class="weight-summary">
        <div class="weight-item">
          <span class="weight-label">Current:</span>
          <span class="weight-value">{{ profile?.weight_kg }} kg</span>
        </div>
        <div class="weight-item" v-if="profile?.target_weight_kg">
          <span class="weight-label">Target:</span>
          <span class="weight-value">{{ profile.target_weight_kg }} kg</span>
        </div>
        <div class="weight-item" v-if="weightChange !== null">
          <span class="weight-label">Change:</span>
          <span class="weight-value" :class="weightChangeClass">
            {{ weightChange > 0 ? '+' : '' }}{{ weightChange.toFixed(1) }} kg
          </span>
        </div>
      </div>
      <div v-if="weightHistory.length > 1" class="weight-trend">
        <h3>Recent Entries</h3>
        <table class="weight-table">
          <thead>
          <tr>
            <th>Date</th>
            <th>Weight</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="entry in recentEntries" :key="entry.id">
            <td>{{ formatDate(entry.recorded_at) }}</td>
            <td>{{ entry.weight_kg }} kg</td>
          </tr>
          </tbody>
        </table>
      </div>
      <button @click="$emit('add-weight')" class="btn btn-secondary">
        Log New Weight
      </button>
    </div>
  </dashboard-card>
</template>

<script>
import DashboardCard from './DashboardCard.vue';
import WellnessService from '../../services/wellness-service';

export default {
  name: 'WeightHistoryCard',
  components: {
    DashboardCard
  },
  props: {
    profile: {
      type: Object,
      default: null
    },
    weightHistory: {
      type: Array,
      default: () => []
    },
    weightChange: {
      type: Number,
      default: null
    },
    error: {
      type: String,
      default: null
    }
  },
  computed: {
    weightChangeClass() {
      return WellnessService.evaluateWeightChange(this.weightChange, this.profile?.fitness_goal);
    },
    recentEntries() {
      if (!this.weightHistory || !this.weightHistory.length) return [];

      return [...this.weightHistory]
          .sort((a, b) => new Date(b.recorded_at) - new Date(a.recorded_at))
          .slice(0, 5);
    }
  },
  methods: {
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