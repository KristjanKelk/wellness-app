// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import Profile from '../views/Profile.vue'

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
    }
]

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes
})

router.beforeEach((to, from, next) => {
    // Check if user is logged in
    const loggedIn = localStorage.getItem('user') !== null;
    console.log(`Route navigation: ${from.path} -> ${to.path}, auth status: ${loggedIn ? 'logged in' : 'not logged in'}`);

    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!loggedIn) {
            console.log('Auth required but not logged in, redirecting to login');
            next({ path: '/login' });
        } else {
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