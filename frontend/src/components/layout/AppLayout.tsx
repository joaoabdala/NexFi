import { Suspense, useState } from "react"
import { Outlet, useLocation } from "react-router-dom"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import { PageFallback } from "@/components/PageFallback"
import { Sidebar, SidebarContent } from "./Sidebar"
import { Topbar } from "./Topbar"
import { AppFooter } from "@/components/AppFooter"

export function AppLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      <Sidebar />

      {mobileNavOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            aria-label="Fechar menu"
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileNavOpen(false)}
          />
          <div className="relative h-full w-64 bg-card shadow-lg">
            <SidebarContent onNavigate={() => setMobileNavOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onOpenMobileNav={() => setMobileNavOpen(true)} />
        <main className="flex flex-1 flex-col overflow-y-auto scrollbar-thin">
          <div key={location.pathname} className="animate-nexfi-page-in flex-1 p-4 lg:p-6">
            {/* Suspense aqui mantém sidebar/topbar visíveis enquanto a página carrega */}
            {/* Boundary por página: um erro numa tela não derruba sidebar/topbar; como o div pai
                tem key=pathname, navegar para outra rota reseta o erro. */}
            <ErrorBoundary>
              <Suspense fallback={<PageFallback />}>
                <Outlet />
              </Suspense>
            </ErrorBoundary>
          </div>
          <AppFooter className="mt-8" />
        </main>
      </div>
    </div>
  )
}
