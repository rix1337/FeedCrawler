import {fileURLToPath, URL} from 'url'

import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    base: './',
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:9090',
                changeOrigin: true
            },
            '/sponsors_helper/api': {
                target: 'http://127.0.0.1:9090',
                changeOrigin: true
            },
        },
    },
    resolve: {
        alias: {
            "@": fileURLToPath(new URL('./src', import.meta.url)),
            "~bootstrap": "bootstrap",
        }
    },
    css: {
        preprocessorOptions: {
            scss: {
                additionalData: "@import '@/assets/scss/variables';",
            }
        }
    },
    build: {}
})
