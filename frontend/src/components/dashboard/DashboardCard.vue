<!-- src/components/dashboard/DashboardCard.vue -->
<template>
  <div class="dashboard-card">
    <h2 class="dashboard-card__title">{{ title }}</h2>
    <div v-if="loading" class="dashboard-card__loading">
      <div class="loading-spinner"></div>
      <p>{{ loadingText }}</p>
    </div>
    <div v-else-if="error" class="dashboard-card__error">
      <p class="error-text">{{ error }}</p>
      <slot name="error-action"></slot>
    </div>
    <div v-else-if="isEmpty" class="dashboard-card__empty">
      <slot name="empty"></slot>
    </div>
    <div v-else class="dashboard-card__body">
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

<style lang="scss" scoped>
</style>