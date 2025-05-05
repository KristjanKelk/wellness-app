<template>
  <div class="form-group">
    <label v-if="label" :for="id" class="form-label">{{ label }}</label>
    <div class="input-wrapper">
      <input
        :id="id"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :maxlength="maxlength"
        :pattern="pattern"
        :inputmode="inputmode"
        class="form-control"
        :class="{ 'error': error }"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    </div>
    <small v-if="error" class="error-text">{{ error }}</small>
    <small v-else-if="helpText" class="help-text">{{ helpText }}</small>
  </div>
</template>

<script>
export default {
  name: 'FormInput',
  props: {
    modelValue: {
      type: [String, Number],
      default: ''
    },
    id: {
      type: String,
      required: true
    },
    label: {
      type: String,
      default: ''
    },
    type: {
      type: String,
      default: 'text'
    },
    placeholder: {
      type: String,
      default: ''
    },
    helpText: {
      type: String,
      default: ''
    },
    error: {
      type: String,
      default: ''
    },
    disabled: {
      type: Boolean,
      default: false
    },
    required: {
      type: Boolean,
      default: false
    },
    maxlength: {
      type: String,
      default: null
    },
    pattern: {
      type: String,
      default: null
    },
    inputmode: {
      type: String,
      default: null
    }
  },
  emits: ['update:modelValue']
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.input-wrapper {
  position: relative;
}

.form-control.error {
  border-color: $error;

  &:focus {
    box-shadow: 0 0 0 3px rgba($error, 0.1);
  }
}

.error-text {
  display: block;
  color: $error;
  margin-top: $spacing-1;
  font-size: $font-size-sm;
}

.help-text {
  display: block;
  color: $gray;
  margin-top: $spacing-1;
  font-size: $font-size-sm;
}
</style>