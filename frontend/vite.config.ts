import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
        },
    },
    server: {
        port: 3000,
        host: '0.0.0.0', // Allow external connections
        allowedHosts: [
            'localhost',
            '127.0.0.1',
            '.ngrok.io',
            '.ngrok-free.dev',
            '.ngrok.app'
        ]
    },
    css: {
        preprocessorOptions: {
            scss: {
                api: 'modern-compiler',
            },
        },
    },
    test: {
        environment: 'jsdom',
        globals: true,
    },
});
