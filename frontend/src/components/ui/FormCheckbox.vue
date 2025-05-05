<template>
  <div class="checkbox-wrapper">
    <input
      :id="id"
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      class="checkbox-input"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <label :for="id" class="checkbox-label">
      <slot>{{ label }}</slot>
    </label>
  </div>
</template>

<script>
export default {
  name: 'FormCheckbox',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    id: {
      type: String,
      required: true
    },
    label: {
      type: String,
      default: ''
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue']
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';

.checkbox-wrapper {
  display: flex;
  align-items: center;
  position: relative;
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;

  &:checked + .checkbox-label:before {
    background-color: $primary;
    border-color: $primary;
  }

  &:checked + .checkbox-label:after {
    opacity: 1;
  }

  &:disabled + .checkbox-label {
    cursor: not-allowed;
    opacity: 0.6;
  }

  &:focus + .checkbox-label:before {
    box-shadow: 0 0 0 3px rgba($primary, 0.2);
  }
}

.checkbox-label {
  padding-left: 28px;
  position: relative;
  cursor: pointer;
  user-select: none;
  display: inline-block;

  &:before {
    content: '';
    position: absolute;
    left: 0;
    top: 2px;
    width: 18px;
    height: 18px;
    border: 2px solid $gray-light;
    border-radius: $border-radius-sm;
    background-color: $white;
    transition: $transition-base;
  }

  &:after {
    content: '';
    position: absolute;
    left: 6px;
    top: 7px;
    width: 6px;
    height: 10px;
    border: solid $white;
    border-width: 0 2px 2px 0;
    transform: rotate(45deg);
    opacity: 0;
    transition: opacity 0.2s;
  }

  &:hover:before {
    border-color: $primary;
  }
}
</style>