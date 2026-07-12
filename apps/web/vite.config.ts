import path from 'path'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { sentryVitePlugin } from '@sentry/vite-plugin'

export default defineConfig({
  plugins: [
    react(),
    // Upload sourcemaps on build. No-op when SENTRY_AUTH_TOKEN is unset, so
    // local dev builds don't fail without the token.
    sentryVitePlugin({
      org: 'brandtech-4o',
      project: 'runmycrew-web',
      authToken: process.env.SENTRY_AUTH_TOKEN,
      disable: !process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
  build: {
    // Required for the plugin to find + upload maps + then strip them from
    // the deployed bundle.
    sourcemap: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  optimizeDeps: {
    // CJS packages — Vite needs to pre-bundle so default exports unwrap properly.
    include: ['react-simple-code-editor', 'prismjs', 'prismjs/components/prism-json'],
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // Playwright owns e2e/ — vitest must not pick up its *.spec.ts.
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
})
