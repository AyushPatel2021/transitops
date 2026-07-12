import { createRouter, createWebHistory } from 'vue-router';
import { useAuth } from '../core/useAuth';
import { useUserStore } from '../stores/userStore';

const routes = [
    {
        path: '/',
        name: 'Landing',
        component: () => import('../views/LandingView.vue'),
        meta: { guest: true }
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/auth/LoginView.vue'),
        meta: { guest: true }
    },
    {
        path: '/signup',
        name: 'Signup',
        component: () => import('../views/auth/SignupView.vue'),
        meta: { guest: true }
    },
    {
        path: '/forgot-password',
        name: 'ForgotPassword',
        component: () => import('../views/auth/ForgotPasswordView.vue'),
        meta: { guest: true }
    },
    {
        path: '/reset-password',
        name: 'ResetPassword',
        component: () => import('../views/auth/ResetPasswordView.vue'),
        meta: { guest: true }
    },
    {
        path: '/auth/google/callback',
        name: 'GoogleCallback',
        component: () => import('../views/auth/GoogleCallbackView.vue'),
        meta: { guest: true }
    },
    {
        path: '/dashboard',
        component: () => import('../components/layout/MainLayout.vue'),
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                name: 'Dashboard',
                component: () => import('../views/DashboardView.vue')
            },
            {
                path: '/models/:model',
                name: 'ModelList',
                component: () => import('../views/GenericView.vue'),
                props: (route: any) => ({ model: route.params.model, title: route.params.model.charAt(0).toUpperCase() + route.params.model.slice(1) })
            },
            {
                path: '/models/:model/:id',
                name: 'ModelDetail',
                component: () => import('../views/GenericView.vue'),
                props: (route: any) => ({ model: route.params.model, title: route.params.model.charAt(0).toUpperCase() + route.params.model.slice(1), initialId: route.params.id })
            },
            {
                path: '/profile',
                name: 'Profile',
                component: () => import('../views/ProfileView.vue'),
                meta: { title: 'My Profile' }
            },
        ]
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('../views/NotFoundView.vue')
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

router.beforeEach(async (to, from, next) => {
    const { isAuthenticated } = useAuth();
    const userStore = useUserStore();
    
    // If we have a token but no user data and not already loading/initializing, try to initialize user first
    if (userStore.token && !userStore.userData && !userStore.isLoading && !userStore.isInitializing) {
        try {
            await userStore.initializeUser();
        } catch (error) {
            // If initialization fails, clear the token and redirect to login
            await userStore.logout();
        }
    }
    
    if (to.meta.requiresAuth && !isAuthenticated.value) {
        next('/login');
    } else if (to.meta.guest && isAuthenticated.value) {
        // If user is authenticated and tries to access guest pages, redirect to dashboard
        next('/dashboard');
    } else {
        next();
    }
});

export default router;
