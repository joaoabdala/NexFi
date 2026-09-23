import { api } from "@/lib/api"
import type { Institution } from "@/types"

export interface InstitutionInput {
  name: string
  short_name?: string | null
  active?: boolean
  note?: string | null
}

export const institutionsApi = {
  list: () => api.get<Institution[]>("/institutions").then((r) => r.data),
  create: (payload: InstitutionInput) => api.post<Institution>("/institutions", payload).then((r) => r.data),
  update: (id: string, payload: Partial<InstitutionInput>) =>
    api.put<Institution>(`/institutions/${id}`, payload).then((r) => r.data),
  deactivate: (id: string) => api.delete(`/institutions/${id}`),
}
