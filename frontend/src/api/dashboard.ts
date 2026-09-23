import { api } from "@/lib/api"
import type { Dashboard } from "@/types"

export const dashboardApi = {
  get: (period: string) => api.get<Dashboard>("/dashboard", { params: { period } }).then((r) => r.data),
}
