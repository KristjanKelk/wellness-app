<template>
  <div class="auth-container">
    <div class="auth-form-container">
      <h2 class="text-center">Sign In</h2>

      <form @submit.prevent="handleLogin">
        <!-- Standard login form -->
        <div v-if="!showTwoFactorForm">
          <FormInput
            id="username"
            label="Username"
            placeholder="Enter your username"
            v-model="username"
            :disabled="loading"
            required
          />

          <FormInput
            id="password"
            type="password"
            label="Password"
            placeholder="Enter your password"
            v-model="password"
            :disabled="loading"
            required
          />

          <div class="form-group">
            <FormCheckbox
              id="remember"
              v-model="remember"
              :disabled="loading"
            >
              Remember me
            </FormCheckbox>
          </div>
        </div>

        <!-- 2FA form -->
        <div v-else class="two-factor-form">
          <p>Please enter the verification code from your authenticator app.</p>
          <FormInput
            id="twoFactorCode"
            label="Verification Code"
            placeholder="000000"
            maxlength="6"
            pattern="[0-9]*"
            inputmode="numeric"
            v-model="twoFactorCode"
            :disabled="loading"
            ref="twoFactorInput"
          />
        </div>

        <!-- Alert for messages -->
        <Alert
          :message="message"
          :type="successful ? 'success' : 'error'"
          v-if="message"
        />

        <!-- Submit button -->
        <BaseButton
          type="submit"
          variant="primary"
          block
          :loading="loading"
          :loading-text="showTwoFactorForm ? 'Verifying...' : 'Signing in...'"
        >
          {{ showTwoFactorForm ? 'Verify' : 'Sign In' }}
        </BaseButton>

        <!-- 2FA cancelation link -->
        <div v-if="showTwoFactorForm" class="form-group text-center mt-4">
          <BaseButton
            variant="text"
            @click="cancelTwoFactor"
          >
            Back to Login
          </BaseButton>
        </div>

        <!-- Links to other auth pages -->
        <div class="form-group text-center mt-4">
          <p>
            <router-link to="/reset-password">Forgot Password?</router-link>
          </p>
          <p class="mt-2">
            Don't have an account?
            <router-link to="/register">Register here</router-link>
          </p>
        </div>
      </form>
    </div>

    <!-- Social login section -->
    <div class="social-login-container">
      <div class="divider">
        <span>OR</span>
      </div>

      <!-- Google login button -->
      <SocialLoginButton
        provider="google"
        :loading="googleLoading"
        :disabled="loading"
        @click="loginWithGoogle"
      >
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

      <!-- GitHub login button -->
      <SocialLoginButton
        provider="github"
        :loading="githubLoading"
        :disabled="loading"
        @click="loginWithGitHub"
      >
        <template #icon>
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
            <path fill="#24292F" d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
          </svg>
        </template>
        Continue with GitHub
      </SocialLoginButton>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import OAuthService from '@/services/oauth.service';
import BaseButton from '@/components/ui/BaseButton.vue';
import FormInput from '@/components/ui/FormInput.vue';
import FormCheckbox from '@/components/ui/FormCheckbox.vue';
import Alert from '@/components/ui/Alert.vue';
import SocialLoginButton from '@/components/ui/SocialLoginButton.vue';

export default {
  name: 'Login',
  components: {
    BaseButton,
    FormInput,
    FormCheckbox,
    Alert,
    SocialLoginButton
  },
  setup() {
    const store = useStore();
    const router = useRouter();

    // Form state
    const username = ref('');
    const password = ref('');
    const twoFactorCode = ref('');
    const remember = ref(false);
    const showTwoFactorForm = ref(false);
    const twoFactorInput = ref(null);
    const tempAuthData = ref(null);

    // UI state
    const loading = ref(false);
    const googleLoading = ref(false);
    const githubLoading = ref(false);
    const message = ref('');
    const successful = ref(false);

    // Computed properties
    const loggedIn = computed(() => store.getters['auth/isLoggedIn']);

    // Check login status on creation
    if (loggedIn.value) {
      router.push('/dashboard');
    }

    // Watch for 2FA form toggle to focus on input
    watch(showTwoFactorForm, async (newVal) => {
      if (newVal && twoFactorInput.value) {
        await nextTick();
        twoFactorInput.value.$el.querySelector('input').focus();
      }
    });

    // Form submission
    const handleLogin = async () => {
      if (showTwoFactorForm.value) {
        await verifyTwoFactor();
        return;
      }

      if (!username.value || !password.value) {
        message.value = 'Please enter both username and password';
        successful.value = false;
        return;
      }

      try {
        loading.value = true;
        message.value = '';

        console.log(`Attempting to login with username: ${username.value}`);

        const userData = await store.dispatch('auth/login', {
          username: username.value,
          password: password.value,
          remember: remember.value
        });

        // Check if 2FA is required
        if (userData.two_factor_enabled) {
          showTwoFactorForm.value = true;
          tempAuthData.value = userData;
          loading.value = false;
        } else {
          // No 2FA, proceed with login
          loginSuccess(userData);
        }
      } catch (error) {
        handleLoginError(error);
      }
    };

    const verifyTwoFactor = async () => {
      if (!twoFactorCode.value || twoFactorCode.value.length !== 6 || !/^\d+$/.test(twoFactorCode.value)) {
        message.value = 'Please enter a valid 6-digit verification code';
        successful.value = false;
        return;
      }

      try {
        loading.value = true;
        message.value = '';

        const userData = await store.dispatch('auth/verifyTwoFactor', {
          code: twoFactorCode.value,
          tempAuthData: tempAuthData.value
        });

        loginSuccess(userData);
      } catch (error) {
        loading.value = false;
        successful.value = false;
        console.error('Login error:', error);

        if (error.response?.data?.detail) {
          message.value = error.response.data.detail;
        } else {
          message.value = 'Invalid verification code. Please try again.';
        }
      }
    };

    const loginSuccess = (userData) => {

      if (!store.getters['auth/isLoggedIn']) {
        store.commit('auth/loginSuccess', userData);
      }

      successful.value = true;
      message.value = 'Login successful! Redirecting...';

      setTimeout(() => {
        router.push('/dashboard');
      }, 500);
    };

    const handleLoginError = (error) => {
      loading.value = false;
      successful.value = false;
      console.error('Login error:', error);

      if (error.response?.data) {
        if (error.response.data.detail) {
          message.value = error.response.data.detail;
        } else if (error.response.data.non_field_errors) {
          message.value = error.response.data.non_field_errors.join(' ');
        } else {
          // Try to extract first error message
          const firstError = Object.values(error.response.data)[0];
          if (Array.isArray(firstError)) {
            message.value = firstError[0];
          } else {
            message.value = 'Failed to login. Please check your credentials.';
          }
        }
      } else {
        message.value = 'Failed to login. Please check your credentials.';
      }
    };

    const cancelTwoFactor = () => {
      showTwoFactorForm.value = false;
      twoFactorCode.value = '';
      tempAuthData.value = null;
    };

    const loginWithGoogle = async () => {
      try {
        message.value = '';
        googleLoading.value = true;

        localStorage.removeItem('oauth_error');

        console.log('Starting Google authentication flow');
        await OAuthService.loginWithGoogle();
      } catch (error) {
        console.error('Google login initialization error:', error);
        message.value = error.message || 'Failed to start Google authentication. Please try again.';
        successful.value = false;
      } finally {
        googleLoading.value = false;
      }
    };

    const loginWithGitHub = async () => {
      try {
        message.value = '';
        githubLoading.value = true;

        localStorage.removeItem('oauth_error');

        console.log('Starting GitHub authentication flow');
        await OAuthService.loginWithGitHub();
      } catch (error) {
        console.error('GitHub login initialization error:', error);
        message.value = error.message || 'Failed to start GitHub authentication. Please try again.';
        successful.value = false;
      } finally {
        githubLoading.value = false;
      }
    };

    return {
      // Form state
      username,
      password,
      twoFactorCode,
      remember,
      showTwoFactorForm,
      twoFactorInput,

      // UI state
      loading,
      googleLoading,
      githubLoading,
      message,
      successful,

      // Methods
      handleLogin,
      verifyTwoFactor,
      cancelTwoFactor,
      loginWithGoogle,
      loginWithGitHub
    };
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/main.scss';

.two-factor-form {
  margin-bottom: $spacing-6;

  p {
    text-align: center;
    margin-bottom: $spacing-6;
    color: $gray;
  }
}
</style>