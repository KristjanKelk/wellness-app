<template>
  <div v-if="message" :class="alertClasses">
    <div class="alert-icon" v-if="type === 'success' || type === 'error'">
      <span v-if="type === 'success'">✓</span>
      <span v-else>!</span>
    </div>
    <div class="alert-content">{{ message }}</div>
    <button
      v-if="dismissible"
      class="alert-close"
      @click="$emit('dismiss')"
      aria-label="Close"
    >
      ×
    </button>
  </div>
</template>

<script>
export default {
  name: 'Alert',
  props: {
    message: {
      type: String,
      default: ''
    },
    type: {
      type: String,
      default: 'info',
      validator: value => ['success', 'error', 'warning', 'info'].includes(value)
    },
    dismissible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['dismiss'],
  computed: {
    alertClasses() {
      return [
        'alert',
        `alert-${this.type}`,
        { 'alert-dismissible': this.dismissible }
      ];
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.alert {
  display: flex;
  align-items: center;
  padding: $spacing-4;
  margin-bottom: $spacing-4;
  border-radius: $border-radius;
  position: relative;
}

.alert-success {
  background-color: mix(white, $success, 90%);
  border: 1px solid $success;
  color: mix(black, $success, 10%);
}

.alert-error {
  background-color: mix(white, $error, 85%);
  border: 1px solid $error;
  color: mix(black, $error, 10%);
}

.alert-warning {
  background-color: mix(white, $warning, 80%);
  border: 1px solid $warning;
  color: mix(black, $warning, 15%);
}

.alert-info {
  background-color: mix(white, $info, 85%);
  border: 1px solid $info;
  color: mix(black, $info, 10%);
}

.alert-dismissible {
  padding-right: $spacing-10;
}

.alert-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  margin-right: $spacing-3;
  flex-shrink: 0;
}

.alert-success .alert-icon {
  background-color: $success;
  color: $white;
}

.alert-error .alert-icon {
  background-color: $error;
  color: $white;
}

.alert-content {
  flex: 1;
}

.alert-close {
  position: absolute;
  top: 50%;
  right: $spacing-4;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  padding: 0;
  cursor: pointer;
  color: inherit;
  opacity: 0.5;
  transition: $transition-base;

  &:hover {
    opacity: 0.75;
  }
}
</style>