import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios"
import { clearTokens, getTokens, setTokens } from "./auth-storage"

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
})

api.interceptors.request.use((config) => {
  const tokens = getTokens()
  if (tokens?.access_token) {
    config.headers.Authorization = `Bearer ${tokens.access_token}`
  }
  return config
})

/** "expired" = o servidor recusou o refresh token (sessão acabou de fato); "unavailable" = falha
 * de rede/5xx/cold start — a sessão pode estar ótima, então não desloga. */
type RefreshResult = { token: string } | "expired" | "unavailable"

let refreshPromise: Promise<RefreshResult> | null = null

async function refreshAccessToken(): Promise<RefreshResult> {
  const tokens = getTokens()
  if (!tokens?.refresh_token) return "expired"
  try {
    const response = await axios.post(`${api.defaults.baseURL}/auth/refresh`, {
      refresh_token: tokens.refresh_token,
    })
    setTokens(response.data)
    return { token: response.data.access_token as string }
  } catch (error) {
    const status = (error as AxiosError).response?.status
    if (status === 401 || status === 403) {
      // Outra aba pode ter renovado primeiro com o mesmo refresh token (ele é rotacionado a cada
      // uso, então o nosso virou inválido). Se o localStorage já tem um par novo, usa esse em
      // vez de deslogar todas as abas.
      const latest = getTokens()
      if (latest && latest.refresh_token !== tokens.refresh_token) return { token: latest.access_token }
      return "expired"
    }
    return "unavailable"
  }
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

// Só as rotas que *emitem* ou *encerram* tokens ficam fora do refresh automático. As demais rotas
// /auth (ex.: GET /auth/me, chamado ao abrir o app) precisam renovar o access token de 15 min —
// senão qualquer F5 depois de 15 minutos mandava o usuário de volta ao login.
const NO_REFRESH_PATHS = ["/auth/login", "/auth/refresh", "/auth/logout"]

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    const skipRefresh = NO_REFRESH_PATHS.some((path) => original?.url?.includes(path))
    if (error.response?.status === 401 && original && !original._retry && !skipRefresh) {
      original._retry = true
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })
      const result = await refreshPromise
      if (typeof result === "object") {
        original.headers.Authorization = `Bearer ${result.token}`
        return api(original)
      }
      if (result === "expired") {
        clearTokens()
        window.location.href = "/login" // recarrega a página: limpa também o cache do React Query
      }
    }
    return Promise.reject(error)
  },
)
