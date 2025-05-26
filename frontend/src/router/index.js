// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import Profile from '../views/Profile.vue'
import Settings from '../views/Settings.vue'
import VerifyEmail from '../views/VerifyEmail.vue'
import ResetPassword from '../views/ResetPassword.vue'
import VerifyPrompt from '../views/VerifyPrompt.vue'
import Activities from '../views/Activities.vue';
import store from '../store'
import OAuthCallback from '../views/OAuthCallback.vue'
import OAuthSuccess from '../views/OAuthSuccess.vue'
import AuthService from '../services/auth.service'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home
    },
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: {
            guest: true
        }
    },
    {
        path: '/register',
        name: 'Register',
        component: Register,
        meta: {
            guest: true
        }
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: {
            requiresAuth: true
        }
    },
    {
        path: '/profile',
        name: 'Profile',
        component: Profile,
        meta: {
            requiresAuth: true
        }
    },
    {
        path: '/settings',
        name: 'Settings',
        component: Settings,
        meta: {
            requiresAuth: true
        }
    },
    {
        path: '/verify-email/:token',
        name: 'VerifyEmail',
        component: VerifyEmail,
        props: true
    },
    {
        path: '/verify-prompt',
        name: 'VerifyPrompt',
        component: VerifyPrompt,
        meta: {
            requiresAuth: true
        }
    },
    {
        path: '/reset-password',
        name: 'RequestPasswordReset',
        component: ResetPassword,
        meta: {
            guest: true
        }
    },
    {
        path: '/reset-password/:token',
        name: 'ResetPassword',
        component: ResetPassword,
        props: true,
        meta: {
            guest: true
        }
    },
    {
        path: '/auth/callback',
        name: 'GenericOAuthCallback',
        component: OAuthCallback
    },
    {
        path: '/auth/callback/:provider',
        name: 'ProviderOAuthCallback',
        component: OAuthCallback,
        props: true
    },
    {
        path: '/auth/success',
        name: 'OAuthSuccess',
        component: OAuthSuccess,
    },
    {
        path: '/auth/success',
        name: 'OAuthSuccess',
        component: OAuthSuccess,
    },
    {
        path: '/design-system',
        name: 'DesignSystem',
        component: () => import('@/views/DesignSystem.vue')
    },
    {
        path: '/progress',
        name: 'Progress',
        component: () => import('@/views/Progress.vue'),
        meta: {
            requiresAuth: true
        }
    },
    {
    path: '/activities',
    name: 'Activities',
    component: Activities,
        meta: {
            requiresAuth: true
        }
    }
]

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes
})

// Give the router access to the store
router.$store = store;

// Update the navigation guard in router/index.js
router.beforeEach((to, from, next) => {
  if (!store || !store.state || !store.state.auth) {
    console.log('Store not fully initialized, proceeding to route');
    next();
    return;
  }

  const isValidToken = AuthService.validateToken();
  const storeLoggedIn = store.getters['auth/isLoggedIn'];

  console.log(`Route navigation: ${from.path} -> ${to.path}, token valid: ${isValidToken}, store logged in: ${storeLoggedIn}`);

  // Sync store state with token validity
  if (storeLoggedIn && !isValidToken) {
    console.log('Inconsistent state: store logged in but token invalid');
    store.commit('auth/logout');
  }

  if (isValidToken && !storeLoggedIn) {
    console.log('Inconsistent state: valid token but store not logged in');
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    try {
      const userData = JSON.parse(userStr);
      store.commit('auth/loginSuccess', userData);
      console.log('Restored user session from storage to store');
    } catch (e) {
      console.error('Failed to restore user session:', e);
    }
  }

  // Re-check login status after potentially fixing inconsistencies
  const loggedIn = store.getters['auth/isLoggedIn'] && isValidToken;

  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!loggedIn) {
      console.log('Auth required but not logged in, redirecting to login');
      next({ path: '/login' });
    } else {
      if (!store.getters['auth/isEmailVerified'] && to.name !== 'VerifyPrompt') {
        console.log('Email not verified, redirecting to verification prompt');
        next({ path: '/verify-prompt' });
        return;
      }

      console.log('Auth required and logged in, proceeding to route');
      next();
    }
  }
  else if (to.matched.some(record => record.meta.guest)) {
    if (loggedIn) {
      console.log('Guest route but already logged in, redirecting to dashboard');
      next({ path: '/dashboard' });
    } else {
      console.log('Guest route and not logged in, proceeding to route');
      next();
    }
  }
  else {
    console.log('Public route, proceeding');
    next();
  }
});

export default router