<template>
  <button
    :class="buttonClasses"
    :type="type"
    :disabled="disabled || loading"
    @click="$emit('click', $event)">
    <span v-if="loading && loadingText">{{ loadingText }}</span>
    <span v-else><slot></slot></span>
  </button>
</template>

<script>
export default {
  name: 'BaseButton',
  props: {
    variant: {
      type: String,
      default: 'primary',
      validator: value => ['primary', 'secondary', 'text', 'danger'].includes(value)
    },
    type: {
      type: String,
      default: 'button'
    },
    block: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    loadingText: {
      type: String,
      default: ''
    }
  },
  computed: {
    buttonClasses() {
      return {
        [`btn-${this.variant}`]: true,
        'btn-block': this.block,
        'btn-loading': this.loading
      };
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.btn-loading {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-2;
}

.loading-spinner {
  @include spinner($size: 1rem, $border-width: 2px, $color: currentColor);
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: currentColor;
  animation: spin 1s linear infinite;
}
</style>