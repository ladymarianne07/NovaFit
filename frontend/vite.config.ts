import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/Logo.png'],
      manifest: {
        name: 'NovaFitness',
        short_name: 'NovaFitness',
        description: 'Seguimiento de nutrición, progreso corporal y entrenamiento.',
        theme_color: '#8b5cf6',
        background_color: '#0f172a',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        scope: '/',
        icons: [
          {
            src: '/icons/Logo.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/Logo.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,json,woff2}'],
        navigateFallbackDenylist: [/^\/api\//],
        clientsClaim: true,
        skipWaiting: false, // Keep false so we can manually trigger skip waiting
      },
      client: {
        installPrompt: true,
        periodicSyncForUpdates: 3600,
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
  server: {
    port: 3000,
    // Only use proxy in development when VITE_API_BASE_URL is not set
    ...(process.env.VITE_API_BASE_URL ? {} : {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    })
  }
})