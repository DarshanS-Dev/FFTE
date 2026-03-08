import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    base: './',
    plugins: [
        react(),
        tailwindcss(),
    ],
    build: {
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'index.html'),
            },
        },
    },
})
