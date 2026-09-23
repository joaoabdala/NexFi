import { api } from "@/lib/api"
import type { User } from "@/types"

export const authApi = {
  updateProfile: (payload: { name?: string; timezone?: string; locale?: string }) =>
    api.patch<User>("/auth/me", payload).then((r) => r.data),
  changePassword: (payload: { current_password: string; new_password: string }) =>
    api.post("/auth/change-password", payload),
}
