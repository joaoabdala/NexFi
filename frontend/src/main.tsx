import { QueryClientProvider } from "@tanstack/react-query"
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import App from "./App.tsx"
import { ToastProvider } from "./components/ui/toaster.tsx"
import { AuthProvider } from "./contexts/AuthContext.tsx"
import { ThemeProvider } from "./contexts/ThemeContext.tsx"
import "./index.css"
import { queryClient } from "./lib/query-client.ts"
import { ErrorBoundary } from "./components/ErrorBoundary.tsx"

// Após um deploy, uma aba aberta com o index.html antigo pede chunks que não existem mais (404).
// Recarrega uma vez para buscar a versão nova; se falhar de novo em seguida, deixa o
// ErrorBoundary mostrar a tela de erro em vez de entrar em loop de reload.
const CHUNK_RELOAD_KEY = "nexfi:chunk-reload-at"
window.addEventListener("vite:preloadError", (event) => {
  try {
    const lastReload = Number(sessionStorage.getItem(CHUNK_RELOAD_KEY) ?? 0)
    if (Date.now() - lastReload < 10_000) return
    sessionStorage.setItem(CHUNK_RELOAD_KEY, String(Date.now()))
  } catch {
    return // sem sessionStorage não dá para evitar loop — melhor mostrar o erro
  }
  event.preventDefault()
  window.location.reload()
})

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AuthProvider>
              <ErrorBoundary>
                <App />
              </ErrorBoundary>
            </AuthProvider>
          </BrowserRouter>
        </QueryClientProvider>
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>,
)
