import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
  // Sem grupos manuais de chunks (vendor/react/charts): com as páginas em React.lazy o Rolldown
  // já isola o Recharts nas páginas com gráfico. Grupos manuais criaram import circular entre
  // chunks e o app quebrava no carregamento em produção ("reading 'create'" do axios).
})
