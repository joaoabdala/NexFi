import { CheckCircle2, XCircle } from "lucide-react"
import { createContext, useCallback, useContext, useState, type ReactNode } from "react"

interface ToastItem {
  id: number
  title: string
  description?: string
  variant: "success" | "error"
}

interface ToastContextValue {
  notify: (toast: Omit<ToastItem, "id">) => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

let idCounter = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const notify = useCallback((toast: Omit<ToastItem, "id">) => {
    const id = ++idCounter
    setToasts((prev) => [...prev, { ...toast, id }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="flex items-start gap-2 rounded-md border border-border bg-card px-4 py-3 shadow-lg min-w-[280px] max-w-sm"
          >
            {toast.variant === "success" ? (
              <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
            ) : (
              <XCircle className="h-5 w-5 shrink-0 text-destructive" />
            )}
            <div>
              <p className="text-sm font-medium">{toast.title}</p>
              {toast.description && <p className="text-xs text-muted-foreground">{toast.description}</p>}
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error("useToast deve ser usado dentro de ToastProvider")
  return ctx
}
