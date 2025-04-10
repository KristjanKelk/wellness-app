<template>
  <div class="modal">
    <div class="modal-content">
      <span class="close-button" @click="$emit('close')">&times;</span>
      <h2>Log New Weight</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="weight">Weight (kg)</label>
          <input
              type="number"
              id="weight"
              v-model="weight"
              step="0.1"
              required
              min="20"
              max="300"
              placeholder="Enter your weight in kg"
          >
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <div class="form-actions">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading">Saving...</span>
            <span v-else>Save</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AddWeightModal',
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      weight: null
    };
  },
  methods: {
    handleSubmit() {
      if (!this.weight || this.weight < 20 || this.weight > 300) {
        this.$emit('error', 'Please enter a valid weight between 20 and 300 kg');
        return;
      }
      this.$emit('save', this.weight);
    }
  }
};
</script>