<!-- src/components/dashboard/BmiStatusCard.vue -->
<template>
  <dashboard-card
    title="BMI Status"
    :isEmpty="bmi === null"
  >
    <template v-slot:empty>
      <p>Your BMI will be calculated once you've added your height and weight.</p>
      <router-link to="/profile" class="btn btn-primary">Update Profile</router-link>
    </template>

    <div class="bmi-container">
      <div class="bmi-value">{{ bmi.toFixed(1) }}</div>
      <div class="bmi-category">{{ bmiCategory }}</div>
      <div class="bmi-scale">
        <div class="bmi-scale-bar">
          <div class="bmi-marker" :style="{ left: markerPosition + '%' }"></div>
          <div class="bmi-segments">
            <div class="segment underweight">Underweight</div>
            <div class="segment normal">Normal</div>
            <div class="segment overweight">Overweight</div>
            <div class="segment obese">Obese</div>
          </div>
        </div>
      </div>
    </div>
  </dashboard-card>
</template>

<script>
import DashboardCard from './DashboardCard.vue';
import WellnessService from '../../services/wellness-service';

export default {
  name: 'BmiStatusCard',
  components: {
    DashboardCard
  },
  props: {
    bmi: {
      type: Number,
      default: null
    },
    profile: {
      type: Object,
      default: null
    }
  },
  computed: {
    bmiCategory() {
      return WellnessService.getBMICategory(this.bmi);
    },
    markerPosition() {
      if (this.bmi === null) return 0;
      const position = Math.min(Math.max(this.bmi, 15), 40) - 15;
      return (position / 25) * 100;
    }
  }
};
</script>