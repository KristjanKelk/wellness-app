// src/components/profile/FitnessAssessment.vue

<template>
  <div class="fitness-assessment">
    <h2>Initial Fitness Assessment</h2>
    <p class="description">
      This information helps us provide more personalized fitness recommendations and track your progress.
    </p>

    <div class="form-section">
      <h3>Current Activity Level</h3>

      <div class="form-group">
        <label for="weeklyActivityDays">How many days per week do you currently exercise?</label>
        <input
          type="number"
          id="weeklyActivityDays"
          v-model="assessment.weekly_activity_days"
          min="0"
          max="7"
          class="form-control"
        />
        <small>Enter a number between 0 and 7</small>
      </div>

      <div class="form-group">
        <label>What types of exercise do you currently do?</label>
        <div class="checkbox-group">
          <div class="checkbox-item">
            <input type="checkbox" id="cardio" v-model="assessment.does_cardio" />
            <label for="cardio">Cardio (running, cycling, swimming, etc.)</label>
          </div>
          <div class="checkbox-item">
            <input type="checkbox" id="strength" v-model="assessment.does_strength" />
            <label for="strength">Strength Training (weights, resistance, etc.)</label>
          </div>
          <div class="checkbox-item">
            <input type="checkbox" id="flexibility" v-model="assessment.does_flexibility" />
            <label for="flexibility">Flexibility (yoga, stretching, etc.)</label>
          </div>
          <div class="checkbox-item">
            <input type="checkbox" id="sports" v-model="assessment.does_sports" />
            <label for="sports">Sports (team sports, racket sports, etc.)</label>
          </div>
        </div>
      </div>
    </div>

    <div class="form-section">
      <h3>Workout Details</h3>

      <div class="form-group">
        <label for="sessionDuration">Average workout duration</label>
        <select id="sessionDuration" v-model="assessment.avg_session_duration" class="form-control">
          <option value="">Select duration</option>
          <option value="short">15-30 minutes</option>
          <option value="medium">30-60 minutes</option>
          <option value="long">60+ minutes</option>
        </select>
      </div>

      <div class="form-group">
        <label for="fitnessLevel">How would you rate your current fitness level?</label>
        <select id="fitnessLevel" v-model="assessment.fitness_level" class="form-control">
          <option value="">Select level</option>
          <option value="beginner">Beginner - New to regular exercise</option>
          <option value="intermediate">Intermediate - Regularly active for 3+ months</option>
          <option value="advanced">Advanced - Consistently training for 1+ years</option>
        </select>
      </div>
    </div>

    <div class="form-section">
      <h3>Preferences</h3>

      <div class="form-group">
        <label for="environment">Preferred exercise environment</label>
        <select id="environment" v-model="assessment.preferred_environment" class="form-control">
          <option value="">Select preference</option>
          <option value="home">Home</option>
          <option value="gym">Gym</option>
          <option value="outdoors">Outdoors</option>
        </select>
      </div>

      <div class="form-group">
        <label for="timePreference">Preferred time to exercise</label>
        <select id="timePreference" v-model="assessment.time_preference" class="form-control">
          <option value="">Select time</option>
          <option value="morning">Morning</option>
          <option value="afternoon">Afternoon</option>
          <option value="evening">Evening</option>
        </select>
      </div>
    </div>

    <div class="form-section">
      <h3>Physical Capacity</h3>

      <div class="form-group">
        <label for="endurance">How long can you walk/run continuously? (minutes)</label>
        <input
          type="number"
          id="endurance"
          v-model="assessment.endurance_minutes"
          min="0"
          class="form-control"
        />
      </div>

      <div class="form-group">
        <label for="pushups">Maximum number of pushups you can do in one set</label>
        <input
          type="number"
          id="pushups"
          v-model="assessment.pushup_count"
          min="0"
          class="form-control"
        />
      </div>

      <div class="form-group">
        <label for="squats">Maximum number of bodyweight squats you can do in one set</label>
        <input
          type="number"
          id="squats"
          v-model="assessment.squat_count"
          min="0"
          class="form-control"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FitnessAssessment',
  props: {
    value: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      assessment: {
        weekly_activity_days: this.value.weekly_activity_days || 0,
        does_cardio: this.value.does_cardio || false,
        does_strength: this.value.does_strength || false,
        does_flexibility: this.value.does_flexibility || false,
        does_sports: this.value.does_sports || false,
        avg_session_duration: this.value.avg_session_duration || '',
        fitness_level: this.value.fitness_level || '',
        preferred_environment: this.value.preferred_environment || '',
        time_preference: this.value.time_preference || '',
        endurance_minutes: this.value.endurance_minutes || null,
        pushup_count: this.value.pushup_count || null,
        squat_count: this.value.squat_count || null
      }
    };
  },
  watch: {
    value: {
      handler(newVal) {
        // Update the assessment data when props change
        Object.keys(newVal).forEach(key => {
          if (key in this.assessment) {
            this.assessment[key] = newVal[key];
          }
        });
      },
      deep: true
    },
    assessment: {
      handler(newVal) {
        // Emit input event when assessment changes to update parent component
        this.$emit('input', newVal);
      },
      deep: true
    }
  }
};
</script>

<style scoped>
.fitness-assessment {
  margin-bottom: 2rem;
}

.description {
  margin-bottom: 1.5rem;
  color: #666;
}

.form-section {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.form-section h3 {
  margin-bottom: 1rem;
  font-size: 1.2rem;
  color: #4CAF50;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.checkbox-group {
  margin-top: 0.5rem;
}

.checkbox-item {
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
}

.checkbox-item input[type="checkbox"] {
  margin-right: 0.5rem;
}

small {
  display: block;
  color: #666;
  margin-top: 0.25rem;
  font-size: 0.8rem;
}
</style>