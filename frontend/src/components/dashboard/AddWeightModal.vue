<!-- src/components/dashboard/AddWeightModal.vue -->
<template>
  <div class="modal is-active" @click.self="$emit('close')">
    <div class="modal-content">
      <span class="close-button" @click="$emit('close')">&times;</span>
      <h2>Log New Weight</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="weight" class="form-label">Weight (kg)</label>
          <input
              type="number"
              id="weight"
              v-model="weight"
              step="0.1"
              required
              min="20"
              max="300"
              placeholder="Enter your weight in kg"
              class="form-control"
          >
        </div>
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <div class="form-actions">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="loading-spinner"></span>
            <span>{{ loading ? 'Saving...' : 'Save' }}</span>
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

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.modal {
  @include modal-container;

  .modal-content {
    @include modal-content;
    max-width: 500px;
    width: 90%;
    animation: fadeIn 0.3s ease-out;
  }

  .close-button {
    position: absolute;
    top: $spacing-4;
    right: $spacing-4;
    font-size: 1.5rem;
    background: none;
    border: none;
    color: $gray;
    cursor: pointer;
    padding: $spacing-2;

    &:hover {
      color: $secondary;
    }
  }

  h2 {
    margin-bottom: $spacing-6;
    text-align: center;
  }

  .form-info {
    margin-bottom: $spacing-4;
  }

  .alert {
    margin-bottom: $spacing-4;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>