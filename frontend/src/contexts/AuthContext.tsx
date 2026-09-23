import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { api } from "@/lib/api"
import { clearTokens, getTokens, setTokens } from "@/lib/auth-storage"
import { queryClient } from "@/lib/query-client"
import type { User } from "@/types"

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  async function refreshUser() {
    const tokens = getTokens()
    if (!tokens) {
      setUser(null)
      setIsLoading(false)
      return
    }
    try {
      const response = await api.get<User>("/auth/me")
      setUser(response.data)
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void refreshUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function login(email: string, password: string) {
    const form = new URLSearchParams()
    form.set("username", email)
    form.set("password", password)
    const response = await api.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    })
    // Nenhuma chave de query inclui o id do usuário: sem limpar, quem loga na mesma aba veria
    // por alguns segundos os dados financeiros em cache do usuário anterior.
    queryClient.clear()
    setTokens(response.data)
    await refreshUser()
  }

  async function logout() {
    const tokens = getTokens()
    if (tokens?.refresh_token) {
      try {
        await api.post("/auth/logout", { refresh_token: tokens.refresh_token })
      } catch {
        // ignora falha de rede no logout — o token local será limpo de qualquer forma
      }
    }
    clearTokens()
    queryClient.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider")
  return ctx
}
