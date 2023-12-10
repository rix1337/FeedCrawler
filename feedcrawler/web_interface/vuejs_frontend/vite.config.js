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
    build: {
        rollupOptions: {
            output: {
                manualChunks(id) {
                    if (id.includes('node_modules')) {
                        return id.toString().split('node_modules/')[1].split('/')[0].toString();
                    }
                }
            }
        }
    }
})
