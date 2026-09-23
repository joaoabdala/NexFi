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

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const tokens = getTokens()
  if (!tokens?.refresh_token) return null
  try {
    const response = await axios.post(`${api.defaults.baseURL}/auth/refresh`, {
      refresh_token: tokens.refresh_token,
    })
    setTokens(response.data)
    return response.data.access_token as string
  } catch {
    clearTokens()
    return null
  }
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    if (error.response?.status === 401 && original && !original._retry && !original.url?.includes("/auth/")) {
      original._retry = true
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })
      const newToken = await refreshPromise
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`
        return api(original)
      }
      clearTokens()
      window.location.href = "/login"
    }
    return Promise.reject(error)
  },
)
