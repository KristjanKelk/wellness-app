<template>
  <div class="form-select-wrapper">
    <label v-if="label" :for="id" :class="['form-label', { 'form-label--required': required }]">
      {{ label }}
    </label>
    
    <div class="form-select-container" :class="{ 'form-select-container--error': hasError }">
      <select 
        :id="id"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :disabled="disabled"
        :required="required"
        class="form-select"
        :class="{ 'form-select--error': hasError }"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <slot>
          <option 
            v-for="option in options" 
            :key="option.value || option" 
            :value="option.value || option"
          >
            {{ option.label || option.text || option }}
          </option>
        </slot>
      </select>
      
      <div class="form-select-icon">
        <i class="fas fa-chevron-down"></i>
      </div>
    </div>
    
    <div v-if="helpText && !hasError" class="form-text form-text--help">
      {{ helpText }}
    </div>
    
    <div v-if="hasError && errorMessage" class="form-text form-text--error">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'FormSelect',
  emits: ['update:modelValue'],
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
      default: null
    },
    placeholder: {
      type: String,
      default: null
    },
    options: {
      type: Array,
      default: () => []
    },
    disabled: {
      type: Boolean,
      default: false
    },
    required: {
      type: Boolean,
      default: false
    },
    helpText: {
      type: String,
      default: null
    },
    errorMessage: {
      type: String,
      default: null
    },
    hasError: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/variables';

.form-select-wrapper {
  margin-bottom: 1.5rem;
}

.form-select-container {
  position: relative;
  
  &--error {
    .form-select {
      border-color: $error;
      
      &:focus {
        box-shadow: 0 0 0 3px rgba($error, 0.1);
      }
    }
  }
}

.form-select {
  width: 100%;
  padding: $input-padding;
  padding-right: 2.5rem;
  border: 1px solid $input-border-color;
  border-radius: $input-radius;
  font-size: $font-size-base;
  font-family: $font-family-base;
  background-color: $white;
  transition: $transition-base;
  appearance: none;
  cursor: pointer;
  
  &:focus {
    border-color: $input-focus-border-color;
    box-shadow: $input-focus-shadow;
    outline: none;
  }
  
  &:hover:not(:disabled) {
    border-color: $primary-light;
  }
  
  &:disabled {
    background-color: $gray-lighter;
    color: $gray;
    cursor: not-allowed;
    
    & + .form-select-icon {
      color: $gray-light;
    }
  }
  
  // Custom option styling
  option {
    padding: $spacing-2;
    background-color: $white;
    color: $secondary;
    
    &:disabled {
      color: $gray;
    }
    
    &:checked {
      background-color: $primary-light;
      color: $white;
    }
  }
}

.form-select-icon {
  position: absolute;
  right: $spacing-3;
  top: 50%;
  transform: translateY(-50%);
  color: $gray;
  pointer-events: none;
  transition: $transition-base;
  font-size: 0.875rem;
}

.form-select-container:hover .form-select-icon {
  color: $primary;
}

.form-select:focus ~ .form-select-icon {
  color: $primary;
}

// Remove default arrow in IE/Edge
.form-select::-ms-expand {
  display: none;
}

// Custom styling for different sizes
.form-select--sm {
  padding: $spacing-2 $spacing-3;
  padding-right: 2rem;
  font-size: $font-size-sm;
  
  & + .form-select-icon {
    right: $spacing-2;
    font-size: 0.75rem;
  }
}

.form-select--lg {
  padding: $spacing-4 $spacing-5;
  padding-right: 3rem;
  font-size: $font-size-lg;
  
  & + .form-select-icon {
    right: $spacing-4;
    font-size: 1rem;
  }
}

// Modern glass-morphism style variant
.form-select--glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  
  &:focus {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba($primary, 0.6);
  }
}

// Multi-select styling
.form-select[multiple] {
  padding: $spacing-2;
  height: auto;
  min-height: 120px;
  
  option {
    padding: $spacing-2 $spacing-3;
    margin-bottom: $spacing-1;
    border-radius: $border-radius-sm;
    
    &:checked {
      background: linear-gradient(135deg, $primary, $primary-light);
      color: $white;
      font-weight: $font-weight-medium;
    }
  }
  
  & + .form-select-icon {
    display: none;
  }
}
</style>