import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { authApi } from "@/api/auth"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/components/ui/toaster"
import { useAuth } from "@/contexts/AuthContext"
import { getApiErrorMessage } from "@/lib/api-error"
import { setTokens } from "@/lib/auth-storage"

const profileSchema = z.object({
  name: z.string().min(1, "Informe o nome."),
  timezone: z.string().min(1),
  locale: z.string().min(1),
})
type ProfileValues = z.infer<typeof profileSchema>

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Informe a senha atual."),
    new_password: z.string().min(8, "A nova senha deve ter ao menos 8 caracteres."),
    confirm_password: z.string().min(1, "Confirme a nova senha."),
  })
  .refine((v) => v.new_password === v.confirm_password, {
    message: "As senhas não coincidem.",
    path: ["confirm_password"],
  })
type PasswordValues = z.infer<typeof passwordSchema>

export function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const { notify } = useToast()

  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    values: { name: user?.name ?? "", timezone: user?.timezone ?? "America/Sao_Paulo", locale: user?.locale ?? "pt-BR" },
  })

  const profileMutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: async () => {
      await refreshUser()
      notify({ title: "Perfil atualizado.", variant: "success" })
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível atualizar o perfil."), variant: "error" }),
  })

  const passwordForm = useForm<PasswordValues>({ resolver: zodResolver(passwordSchema) })

  const passwordMutation = useMutation({
    mutationFn: (values: PasswordValues) =>
      authApi.changePassword({ current_password: values.current_password, new_password: values.new_password }),
    onSuccess: (tokens) => {
      // A troca encerra todas as sessões; o backend devolve um par novo só para esta aba.
      setTokens(tokens)
      notify({ title: "Senha alterada. Outros dispositivos foram desconectados.", variant: "success" })
      passwordForm.reset()
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível alterar a senha."), variant: "error" }),
  })

  return (
    <div className="flex max-w-xl flex-col gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Perfil</h1>
        <p className="text-sm text-muted-foreground">{user?.email}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados pessoais</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={profileForm.handleSubmit((v) => profileMutation.mutateAsync(v).catch(() => {}))}
            className="flex flex-col gap-4"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Nome</Label>
              <Input id="name" {...profileForm.register("name")} />
              {profileForm.formState.errors.name && (
                <p className="text-xs text-destructive">{profileForm.formState.errors.name.message}</p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="timezone">Fuso horário</Label>
              <Input id="timezone" {...profileForm.register("timezone")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="locale">Idioma / locale</Label>
              <Input id="locale" {...profileForm.register("locale")} />
            </div>
            <Button type="submit" disabled={profileMutation.isPending} className="self-start">
              Salvar alterações
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Alterar senha</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={passwordForm.handleSubmit((v) => passwordMutation.mutateAsync(v).catch(() => {}))}
            className="flex flex-col gap-4"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="current_password">Senha atual</Label>
              <Input id="current_password" type="password" {...passwordForm.register("current_password")} />
              {passwordForm.formState.errors.current_password && (
                <p className="text-xs text-destructive">{passwordForm.formState.errors.current_password.message}</p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="new_password">Nova senha</Label>
              <Input id="new_password" type="password" {...passwordForm.register("new_password")} />
              {passwordForm.formState.errors.new_password && (
                <p className="text-xs text-destructive">{passwordForm.formState.errors.new_password.message}</p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="confirm_password">Confirmar nova senha</Label>
              <Input id="confirm_password" type="password" {...passwordForm.register("confirm_password")} />
              {passwordForm.formState.errors.confirm_password && (
                <p className="text-xs text-destructive">{passwordForm.formState.errors.confirm_password.message}</p>
              )}
            </div>
            <Button type="submit" disabled={passwordMutation.isPending} className="self-start">
              Alterar senha
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
