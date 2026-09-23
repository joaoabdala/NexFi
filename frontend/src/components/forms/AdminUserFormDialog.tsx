import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { adminUsersApi } from "@/api/admin"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/components/ui/toaster"
import type { AdminUser } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"

const baseSchema = {
  email: z.string().email("Informe um e-mail válido."),
  name: z.string().min(1, "Informe o nome."),
  role: z.enum(["ADMIN", "USER"]),
  is_active: z.boolean(),
}

const createSchema = z.object({
  ...baseSchema,
  password: z.string().min(8, "A senha deve ter ao menos 8 caracteres."),
})

const editSchema = z.object({
  ...baseSchema,
  password: z.union([z.string().min(8, "A senha deve ter ao menos 8 caracteres."), z.literal("")]),
})

type FormValues = z.infer<typeof createSchema>

export function AdminUserFormDialog({
  open,
  onOpenChange,
  user,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  user?: AdminUser | null
}) {
  const isEditing = !!user
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(isEditing ? editSchema : createSchema),
  })

  useEffect(() => {
    if (open) {
      reset({
        email: user?.email ?? "",
        name: user?.name ?? "",
        role: user?.role ?? "USER",
        is_active: user?.is_active ?? true,
        password: "",
      })
    }
  }, [open, user, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      if (isEditing) {
        const payload = { ...values, password: values.password || undefined }
        return adminUsersApi.update(user!.id, payload)
      }
      return adminUsersApi.create(values)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      notify({ title: isEditing ? "Usuário atualizado." : "Usuário criado.", variant: "success" })
      onOpenChange(false)
    },
    onError: (err: unknown) => {
      const message = getApiErrorMessage(err, "Não foi possível salvar o usuário.")
      notify({ title: message, variant: "error" })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "Editar usuário" : "Novo usuário"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Nome</Label>
            <Input id="name" {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email">E-mail</Label>
            <Input id="email" type="email" {...register("email")} />
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="password">{isEditing ? "Nova senha (deixe em branco para manter)" : "Senha"}</Label>
            <Input id="password" type="password" {...register("password")} />
            {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Papel</Label>
            <Controller
              control={control}
              name="role"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USER">Usuário</SelectItem>
                    <SelectItem value="ADMIN">Administrador</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div className="flex items-center justify-between rounded-md border border-border p-3">
            <div>
              <p className="text-sm font-medium">Conta ativa</p>
              <p className="text-xs text-muted-foreground">Usuários inativos não conseguem fazer login</p>
            </div>
            <Controller
              control={control}
              name="is_active"
              render={({ field }) => <Switch checked={field.value} onCheckedChange={field.onChange} />}
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              Salvar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
