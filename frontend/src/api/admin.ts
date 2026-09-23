import { api } from "@/lib/api"
import type { AdminUser, UserRole } from "@/types"

export interface AdminUserCreateInput {
  email: string
  password: string
  name: string
  role?: UserRole
  is_active?: boolean
}

export interface AdminUserUpdateInput {
  email?: string
  name?: string
  role?: UserRole
  is_active?: boolean
  password?: string
}

export const adminUsersApi = {
  list: () => api.get<AdminUser[]>("/admin/users").then((r) => r.data),
  create: (payload: AdminUserCreateInput) => api.post<AdminUser>("/admin/users", payload).then((r) => r.data),
  update: (id: string, payload: AdminUserUpdateInput) =>
    api.put<AdminUser>(`/admin/users/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/admin/users/${id}`),
}
