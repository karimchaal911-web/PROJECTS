import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Relative base so the bundle can be served from any path, not just a domain
// root. It still needs a local static server rather than file:// — ES modules
// are blocked by CORS there — which is what RUN_PRESENTATION.ps1 provides.
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    target: 'es2022',
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 1800,
    rollupOptions: {
      output: {
        manualChunks: {
          three: ['three'],
          r3f: ['@react-three/fiber', '@react-three/drei'],
        },
      },
    },
  },
  server: { host: '127.0.0.1', port: 5180, strictPort: false },
});
