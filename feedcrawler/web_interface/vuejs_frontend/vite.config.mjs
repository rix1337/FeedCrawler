import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import {fileURLToPath, URL} from 'url'

export default defineConfig({
    plugins: [vue()],
    base: './',
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:9090',
                changeOrigin: true
            },
            '/captcha': {
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
                    // Split all external libraries into a "vendors" chunk
                    if (id.includes('node_modules')) {
                        return 'vendors';
                    }
                    // Split Vue files (*.vue) into separate chunks
                    if (id.endsWith('.vue')) {
                        return 'components';
                    }
                    // Split JavaScript files (*.js) in the `src` directory into separate chunks
                    if (id.includes('src') && id.endsWith('.js')) {
                        const pathParts = id.split('/');
                        const name = pathParts[pathParts.length - 1]; // Get the file name
                        return name.replace('.js', ''); // Use the file name as the chunk name
                    }
                    return null; // Default behavior (no chunk)
                },
            },
        },
    }
})
