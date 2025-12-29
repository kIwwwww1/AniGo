import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Определяем target для прокси
// В Docker используем имя сервиса backend, в локальной разработке - localhost
const proxyTarget = process.env.VITE_API_TARGET || 'http://backend:8000'

console.log('Vite proxy target:', proxyTarget)
console.log('VITE_API_TARGET env:', process.env.VITE_API_TARGET)

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        secure: false, // Для работы с HTTP в dev режиме
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Proxy error:', err.message)
            console.log('Proxy target was:', proxyTarget)
          })
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Proxying request:', req.method, req.url, '->', proxyTarget + proxyReq.path)
          })
        },
      }
    }
  }
})

