// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// Import base styles
import './assets/styles/main.scss'

// Service wake-up helper
import { wakeupService } from './utils/serviceWakeup'

/**
 * Bootstraps the Vue application.
 * Before mounting we try to ping the backend once so the first
 * real API requests don’t hit a sleeping container and fail with 503/timeout.
 * If the wake-up fails we still mount the app, the existing axios
 * interceptors will handle retries when the user performs actions.
 */
async function bootstrap() {
  try {
    // Attempt to wake the service in the background (no progress UI here)
    await wakeupService(false)
    console.log('✅ Backend service is awake')
  } catch (err) {
    console.warn('⚠️  Backend wake-up failed or timed out:', err?.message || err)
    // Continue – axios interceptors will still retry on demand
  }

  const app = createApp(App)
  app.use(store)
  app.use(router)
  app.mount('#app')
}

// Run the bootstrap sequence
bootstrap()