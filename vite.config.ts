import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backendProxy = {
  '/api': 'http://127.0.0.1:8000',
  '/exports': 'http://127.0.0.1:8000',
  '/asset-files': 'http://127.0.0.1:8000',
};

export default defineConfig({
  plugins: [react()],
  server: { host: '0.0.0.0', allowedHosts: true, proxy: backendProxy },
  preview: { host: '0.0.0.0', allowedHosts: true, proxy: backendProxy },
});
