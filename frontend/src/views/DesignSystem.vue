<template>
  <div class="container">
    <h1 class="page-title">Design System</h1>
    <p class="page-description">This page showcases the UI components and styles used in the Wellness Platform.</p>

    <section class="section">
      <h2 class="section-title">Typography</h2>

      <div class="component-example">
        <h1>Heading 1</h1>
        <h2>Heading 2</h2>
        <h3>Heading 3</h3>
        <h4>Heading 4</h4>
        <p>This is a paragraph text. It demonstrates the base font size and line height used throughout the application.</p>
        <p><small>This is small text, used for captions and helper text.</small></p>
        <p><a href="#">This is a link</a></p>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">Colors</h2>

      <div class="color-grid">
        <div class="color-item">
          <div class="color-swatch primary"></div>
          <div class="color-info">
            <span class="color-name">Primary</span>
            <span class="color-code">#30C1B1</span>
          </div>
        </div>

        <div class="color-item">
          <div class="color-swatch primary-dark"></div>
          <div class="color-info">
            <span class="color-name">Primary Dark</span>
            <span class="color-code">#25A59A</span>
          </div>
        </div>

        <div class="color-item">
          <div class="color-swatch primary-light"></div>
          <div class="color-info">
            <span class="color-name">Primary Light</span>
            <span class="color-code">#4FDFD0</span>
          </div>
        </div>

        <div class="color-item">
          <div class="color-swatch secondary"></div>
          <div class="color-info">
            <span class="color-name">Secondary</span>
            <span class="color-code">#212A36</span>
          </div>
        </div>

        <div class="color-item">
          <div class="color-swatch gray-dark"></div>
          <div class="color-info">
            <span class="color-name">Gray Dark</span>
            <span class="color-code">#4A5568</span>
          </div>
        </div>

        <div class="color-item">
          <div class="color-swatch gray"></div>
          <div class="color-info">
            <span class="color-name">Gray</span>
            <span class="color-code">#718096</span>
          </div>
        </div>

        <div class="color-item">
          <div class="color-swatch error"></div>
          <div class="color-info">
            <span class="color-name">Error</span>
            <span class="color-code">#E53E3E</span>
          </div>
        </div>

        <div class="color-item">
          <div class="color-swatch success"></div>
          <div class="color-info">
            <span class="color-name">Success</span>
            <span class="color-code">#38A169</span>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">Buttons</h2>

      <div class="component-example">
        <div class="example-row">
          <BaseButton>Default Button</BaseButton>
          <BaseButton variant="secondary">Secondary Button</BaseButton>
          <BaseButton variant="text">Text Button</BaseButton>
        </div>

        <div class="example-row">
          <BaseButton loading>Loading Button</BaseButton>
          <BaseButton variant="secondary" loading>Loading Secondary</BaseButton>
          <BaseButton disabled>Disabled Button</BaseButton>
        </div>

        <div class="example-row">
          <BaseButton block>Block Button</BaseButton>
        </div>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">Form Inputs</h2>

      <div class="component-example">
        <FormInput
          id="example-input"
          label="Text Input"
          placeholder="Enter text"
          v-model="exampleInput"
        />

        <FormInput
          id="example-input-error"
          label="Input with Error"
          placeholder="Enter text"
          error="This field has an error"
          v-model="exampleInputError"
        />

        <FormInput
          id="example-input-help"
          label="Input with Help"
          placeholder="Enter text"
          helpText="This is a helpful message"
          v-model="exampleInputHelp"
        />

        <FormInput
          id="example-input-password"
          type="password"
          label="Password Input"
          placeholder="Enter password"
          v-model="examplePassword"
        />

        <FormCheckbox
          id="example-checkbox"
          v-model="exampleCheckbox"
        >
          I agree to the terms and conditions
        </FormCheckbox>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">Alerts</h2>

      <div class="component-example">
        <Alert
          message="This is a success message."
          type="success"
        />

        <Alert
          message="This is an error message."
          type="error"
        />

        <Alert
          message="This is a warning message."
          type="warning"
        />

        <Alert
          message="This is an information message."
          type="info"
        />

        <Alert
          message="This is a dismissible alert."
          type="success"
          dismissible
          @dismiss="dismissAlert"
        />
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">Social Login Buttons</h2>

      <div class="component-example">
        <SocialLoginButton provider="google">
          <template #icon>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 48 48">
              <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"></path>
              <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"></path>
              <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"></path>
              <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"></path>
            </svg>
          </template>
          Continue with Google
        </SocialLoginButton>

        <SocialLoginButton provider="github">
          <template #icon>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
              <path fill="#24292F" d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
            </svg>
          </template>
          Continue with GitHub
        </SocialLoginButton>
      </div>
    </section>
  </div>
</template>

<script>
import { ref } from 'vue';
import BaseButton from '@/components/ui/BaseButton.vue';
import FormInput from '@/components/ui/FormInput.vue';
import FormCheckbox from '@/components/ui/FormCheckbox.vue';
import Alert from '@/components/ui/Alert.vue';
import SocialLoginButton from '@/components/ui/SocialLoginButton.vue';

export default {
  name: 'DesignSystem',
  components: {
    BaseButton,
    FormInput,
    FormCheckbox,
    Alert,
    SocialLoginButton
  },
  setup() {
    const exampleInput = ref('');
    const exampleInputError = ref('');
    const exampleInputHelp = ref('');
    const examplePassword = ref('');
    const exampleCheckbox = ref(false);

    const dismissAlert = () => {
      console.log('Alert dismissed');
    };

    return {
      exampleInput,
      exampleInputError,
      exampleInputHelp,
      examplePassword,
      exampleCheckbox,
      dismissAlert
    };
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.page-title {
  margin-top: $spacing-8;
  margin-bottom: $spacing-4;
}

.page-description {
  margin-bottom: $spacing-8;
  color: $gray;
  max-width: 600px;
}

.section {
  margin-bottom: $spacing-12;
  padding-bottom: $spacing-8;
  border-bottom: 1px solid $gray-lighter;

  &:last-child {
    border-bottom: none;
  }
}

.section-title {
  margin-bottom: $spacing-6;
  position: relative;
  display: inline-block;

  &:after {
    content: '';
    position: absolute;
    bottom: -6px;
    left: 0;
    width: 40px;
    height: 3px;
    background-color: $primary;
  }
}

.component-example {
  padding: $spacing-6;
  background-color: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
}

.example-row {
  margin-bottom: $spacing-6;
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-4;
  align-items: center;

  &:last-child {
    margin-bottom: 0;
  }
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: $spacing-6;
}

.color-item {
  display: flex;
  flex-direction: column;
}

.color-swatch {
  width: 100%;
  height: 80px;
  border-radius: $border-radius;
  margin-bottom: $spacing-2;

  &.primary {
    background-color: $primary;
  }

  &.primary-dark {
    background-color: $primary-dark;
  }

  &.primary-light {
    background-color: $primary-light;
  }

  &.secondary {
    background-color: $secondary;
  }

  &.gray-dark {
    background-color: $gray-dark;
  }

  &.gray {
    background-color: $gray;
  }

  &.error {
    background-color: $error;
  }

  &.success {
    background-color: $success;
  }
}

.color-info {
  display: flex;
  flex-direction: column;
}

.color-name {
  font-weight: $font-weight-medium;
}

.color-code {
  color: $gray;
  font-size: $font-size-sm;
}
</style>