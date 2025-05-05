<template>
  <button
    class="social-login-button"
    :class="`social-login-button-${provider}`"
    :disabled="disabled || loading"
    @click="$emit('click')">
    <div v-if="loading" class="loading-spinner"></div>
    <div v-else class="social-icon">
      <slot name="icon"></slot>
    </div>
    <span class="social-text">
      <slot></slot>
    </span>
  </button>
</template>

<script>
export default {
  name: 'SocialLoginButton',
  props: {
    provider: {
      type: String,
      required: true,
      validator: value => ['google', 'github', 'facebook', 'apple'].includes(value)
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click']
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.social-login-button {
  @include button-base;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-3;
  width: 100%;
  background-color: $white;
  color: $secondary;
  border: 1px solid $gray-lighter;
  margin-bottom: $spacing-4;
  transition: $transition-base;

  &:hover:not(:disabled) {
    background-color: $gray-lighter;
  }

  .social-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
  }

  .social-text {
    flex: 1;
    text-align: center;
  }
}

.social-login-button-google {
  &:hover:not(:disabled) {
    background-color: #f8f9fa;
    border-color: #dadce0;
  }
}

.social-login-button-github {
  &:hover:not(:disabled) {
    background-color: #f6f8fa;
    border-color: #e1e4e8;
  }
}

.social-login-button-facebook {
  &:hover:not(:disabled) {
    background-color: #f5f6f7;
    border-color: #dddfe2;
  }
}

.social-login-button-apple {
  background-color: #000;
  color: #fff;
  border-color: #000;

  &:hover:not(:disabled) {
    background-color: #333;
    border-color: #333;
  }
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