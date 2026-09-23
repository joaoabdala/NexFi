import { api } from "@/lib/api"
import type { Category, CategoryKind } from "@/types"

export interface CategoryInput {
  name: string
  kind: CategoryKind
  parent_id?: string | null
  active?: boolean
}

export const categoriesApi = {
  list: () => api.get<Category[]>("/categories").then((r) => r.data),
  create: (payload: CategoryInput) => api.post<Category>("/categories", payload).then((r) => r.data),
  update: (id: string, payload: Partial<CategoryInput>) =>
    api.put<Category>(`/categories/${id}`, payload).then((r) => r.data),
  deactivate: (id: string) => api.delete(`/categories/${id}`),
}
