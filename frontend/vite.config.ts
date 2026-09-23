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
  build: {
    rolldownOptions: {
      output: {
        // Bibliotecas grandes em chunks próprios: mudam raramente, então o cache do
        // navegador sobrevive aos deploys do app. Recharts só é baixado nas páginas com gráfico.
        codeSplitting: {
          // Sem isso, dependências compartilhadas (ex.: clsx) são puxadas para o grupo
          // 'charts' e o Recharts acaba sendo pré-carregado em todas as páginas.
          includeDependenciesRecursively: false,
          groups: [
            { name: 'charts', test: /node_modules[\\/](recharts|d3-|victory-vendor)/, priority: 30 },
            { name: 'react', test: /node_modules[\\/](react|react-dom|react-router|react-router-dom|scheduler)[\\/]/, priority: 20 },
            { name: 'vendor', test: /node_modules[\\/](@radix-ui|@tanstack|axios|date-fns|zod|react-hook-form|@hookform)/, priority: 10 },
          ],
        },
      },
    },
  },
})
