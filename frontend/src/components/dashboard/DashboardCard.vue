<!-- src/components/dashboard/DashboardCard.vue -->
<template>
  <div class="card">
    <h2>{{ title }}</h2>
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ loadingText }}</p>
    </div>
    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <slot name="error-action"></slot>
    </div>
    <div v-else-if="isEmpty" class="empty-container">
      <slot name="empty"></slot>
    </div>
    <div v-else>
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DashboardCard',
  props: {
    title: {
      type: String,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    loadingText: {
      type: String,
      default: 'Loading...'
    },
    error: {
      type: String,
      default: null
    },
    isEmpty: {
      type: Boolean,
      default: false
    }
  }
};
</script>