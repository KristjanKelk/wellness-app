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

router.$store = store;
router.beforeEach((to, from, next) => {
  if (!store || !store.state || !store.state.auth) {
    next();
    return;
  }

  const isValidToken = AuthService.validateToken();
  const storeLoggedIn = store.getters['auth/isLoggedIn'];

  if (storeLoggedIn && !isValidToken) {
    store.commit('auth/logout');
  }

  if (isValidToken && !storeLoggedIn) {
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    try {
      const userData = JSON.parse(userStr);
      store.commit('auth/loginSuccess', userData);
    } catch (e) {
      console.error('Failed to restore user session:', e);
    }
  }

  const loggedIn = store.getters['auth/isLoggedIn'] && isValidToken;

  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!loggedIn) {
      next({ path: '/login' });
    } else {
      if (!store.getters['auth/isEmailVerified'] && to.name !== 'VerifyPrompt') {
        next({ path: '/verify-prompt' });
        return;
      }
      next();
    }
  }
  else if (to.matched.some(record => record.meta.guest)) {
    if (loggedIn) {
      next({ path: '/dashboard' });
    } else {
      next();
    }
  }
  else {
    next();
  }
});

export default router