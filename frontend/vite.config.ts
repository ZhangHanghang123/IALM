import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// IALM 前端 vite 配置（沿用 4 模块风格）
export default defineConfig({
  base: '/ialm/',           // 部署到 https://wxfzhh.online/ialm/
  plugins: [react()],
  server: {
    host: true,
    port: 5174,             // 避免与 IALMD 5173 冲突
    proxy: {
      '/ialm/api': {
        target: 'http://127.0.0.1:8004',   // IALM 后端
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ialm\/api/, '/api'),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 2048,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          antd: ['antd', '@ant-design/icons'],
          charts: ['echarts', 'echarts-for-react'],
        },
      },
    },
  },
})