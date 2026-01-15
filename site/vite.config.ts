import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  // For GitHub Pages deployment, set base to match your repo name
  // Example: base: '/MuseumSpark/' for username.github.io/MuseumSpark/
  // For custom domain or local dev, use: base: '/'
  base: process.env.NODE_ENV === 'production' ? '/MuseumSpark/' : '/',
  plugins: [react(), tailwindcss()],
  server: {
    host: 'localhost',
    port: 5173,
    strictPort: true,
  },
})
