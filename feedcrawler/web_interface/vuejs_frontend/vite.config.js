import {fileURLToPath, URL} from 'url'

import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    base: './',
    server: {
        proxy: {
            '/api': {
                target: 'http://localhost:9090/feedcrawler',
                changeOrigin: true
            },
            '/sponsors_helper/api': {
                target: 'http://localhost:9090/feedcrawler',
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
    }
})
