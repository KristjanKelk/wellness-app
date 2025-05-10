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
          <span class="weight-label">Recent Change:</span>
          <span class="weight-value" :class="weightChangeClass">
            {{ weightChange > 0 ? '+' : '' }}{{ weightChange.toFixed(1) }} kg
          </span>
        </div>
      </div>

      <div v-if="weightHistory.length > 0" class="weight-trend">
        <div class="weight-mini-chart">
          <div
            v-for="(entry, index) in normalizedEntries"
            :key="index"
            class="mini-chart-bar"
            :style="{
              height: entry.height + '%',
              background: getBarColor(entry.value, profile?.fitness_goal)
            }"
            :title="`${formatDate(entry.recorded_at)}: ${entry.value} kg`"
          ></div>
        </div>
      </div>

      <div v-if="weightHistory.length > 1" class="weight-history-list">
        <h3>Recent Entries</h3>
        <table class="weight-table">
          <thead>
          <tr>
            <th>Date & Time</th>
            <th>Weight</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="entry in recentEntries" :key="entry.id">
            <td>{{ formatDateTime(entry.recorded_at) }}</td>
            <td>{{ entry.weight_kg }} kg</td>
          </tr>
          </tbody>
        </table>
      </div>

      <button @click="$emit('add-weight')" class="btn btn-secondary">
        Log New Weight
      </button>

      <div class="view-all-link" v-if="weightHistory.length > 5">
        <router-link to="/progress">View full weight history and charts</router-link>
      </div>
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
    },
    normalizedEntries() {
      if (!this.weightHistory || this.weightHistory.length === 0) return [];

      // Get the last 10 entries or all entries if less than 10
      const entries = [...this.weightHistory]
        .sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at))
        .slice(-10);

      // Find min and max values for normalization
      const weights = entries.map(entry => parseFloat(entry.weight_kg));
      const min = Math.min(...weights);
      const max = Math.max(...weights);

      // Min-max normalization with fixed range (to keep the chart from being too flat)
      const range = Math.max(max - min, 2); // Ensure a minimum range

      return entries.map(entry => ({
        value: parseFloat(entry.weight_kg),
        recorded_at: entry.recorded_at,
        height: ((parseFloat(entry.weight_kg) - min) / range) * 80 + 10 // Scale to 10-90% height
      }));
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
    },
    formatDateTime(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      }) + ' ' + date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    getBarColor(weight, goal) {
      // If no goal or no profile, use neutral color
      if (!goal || !this.profile?.weight_kg) return this.$primary || '#30C1B1';

      // Current weight
      const currentWeight = parseFloat(this.profile.weight_kg);

      // Get colors from variables
      const successColor = getComputedStyle(document.documentElement).getPropertyValue('--success-color') || '#4CAF50';
      const warningColor = getComputedStyle(document.documentElement).getPropertyValue('--warning-color') || '#FF9800';

      // For weight loss goal
      if (goal === 'weight_loss') {
        return weight <= currentWeight ? successColor : warningColor;
      }

      // For muscle gain goal
      if (goal === 'muscle_gain') {
        return weight >= currentWeight ? successColor : warningColor;
      }

      // For other goals, return neutral color
      return '#30C1B1';
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.weight-container {
  padding: $spacing-4 0;
}

.weight-summary {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-4;
  margin-bottom: $spacing-6;
  padding: $spacing-4;
  background-color: $bg-light;
  border-radius: $border-radius;
}

.weight-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.weight-label {
  font-size: $font-size-sm;
  color: $gray;
  margin-bottom: $spacing-1;
}

.weight-value {
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;

  &.positive {
    color: $positive;
  }

  &.negative {
    color: $negative;
  }

  &.neutral {
    color: $neutral;
  }
}

.weight-trend {
  margin-bottom: $spacing-6;
}

.weight-mini-chart {
  display: flex;
  align-items: flex-end;
  height: 100px;
  width: 100%;
  border-bottom: 1px solid $gray-lighter;
  gap: 2px;
}

.mini-chart-bar {
  flex: 1;
  border-radius: 2px 2px 0 0;
  transition: $transition-base;
  position: relative;
  min-width: 10px;
}

.weight-history-list {
  margin-bottom: $spacing-6;

  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-3;
  }
}

.weight-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: $spacing-4;
  font-size: $font-size-sm;

  th {
    background-color: $bg-light;
    padding: $spacing-3;
    text-align: left;
    font-weight: $font-weight-semibold;
  }

  td {
    padding: $spacing-3;
    border-bottom: 1px solid $gray-lighter;
  }
}

.view-all-link {
  margin-top: $spacing-4;
  text-align: center;
}

.btn-secondary {
  width: 100%;
  margin-top: $spacing-4;
}
</style>