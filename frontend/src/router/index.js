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
import store from '../store'

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
    }
]

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes
})

// Give the router access to the store
router.$store = store;

router.beforeEach((to, from, next) => {
    // Use both Vuex store and localStorage to check login status
    // This ensures we catch authentication from both sources
    const storeLoggedIn = store.state.auth && store.state.auth.status && store.state.auth.status.loggedIn;
    const localStorageLoggedIn = localStorage.getItem('user') !== null || sessionStorage.getItem('user') !== null;

    // User is logged in if either source indicates they are
    const loggedIn = storeLoggedIn || localStorageLoggedIn;

    console.log(`Route navigation: ${from.path} -> ${to.path}, auth status: ${loggedIn ? 'logged in' : 'not logged in'}`);
    console.log(`Store logged in: ${storeLoggedIn}, localStorage logged in: ${localStorageLoggedIn}`);

    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!loggedIn) {
            console.log('Auth required but not logged in, redirecting to login');
            next({ path: '/login' });
        } else {
            // Check if email is verified when it's a protected route
            let user = null;

            // Try to get user from store first
            if (store.state.auth && store.state.auth.user) {
                user = store.state.auth.user;
            }
            // If not in store, try localStorage
            else {
                const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
                if (userStr) {
                    try {
                        user = JSON.parse(userStr);
                    } catch (e) {
                        console.error('Error parsing user data:', e);
                    }
                }
            }

            if (user && user.email_verified === false && to.name !== 'VerifyPrompt') {
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