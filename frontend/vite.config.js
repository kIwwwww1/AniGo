import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Определяем target для прокси
// В Docker используем имя сервиса backend, в локальной разработке - localhost
export default defineConfig(({ mode }) => {
  // Загружаем переменные окружения
  const env = loadEnv(mode, process.cwd(), '')
  
  // Определяем target для прокси
  const proxyTarget = env.VITE_API_TARGET || env.API_TARGET || 'http://backend:8000'

  console.log('Vite proxy target:', proxyTarget)
  console.log('VITE_API_TARGET env:', env.VITE_API_TARGET)
  console.log('API_TARGET env:', env.API_TARGET)
  console.log('Mode:', mode)

  return {
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
              console.error('Proxy error:', err.message)
              console.error('Proxy target was:', proxyTarget)
              console.error('Error details:', err)
            })
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Proxying request:', req.method, req.url, '->', proxyTarget + proxyReq.path)
            })
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Proxy response:', req.url, '->', proxyRes.statusCode)
            })
          },
        }
      }
    }
  }
})

