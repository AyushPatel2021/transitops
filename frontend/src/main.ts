import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config';
import Aura from '@primevue/themes/aura';
import App from './App.vue'
import router from './router'
import './styles/theme.css' // Theme CSS variables (must be imported first)
import './styles/base.scss'

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: '[data-theme="dark"]' // Match our theme system
        }
    }
});
app.use(router);
app.mount('#app')
