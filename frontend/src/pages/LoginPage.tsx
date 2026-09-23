import { zodResolver } from "@hookform/resolvers/zod"
import { AlertCircle, Lock, Mail } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { Navigate, useNavigate } from "react-router-dom"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoginVisual } from "@/components/LoginVisual"
import { useAuth } from "@/contexts/AuthContext"
import { getApiErrorMessage } from "@/lib/api-error"

const schema = z.object({
  email: z.string().email("Informe um e-mail válido."),
  password: z.string().min(1, "Informe a senha."),
})

type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  if (user) {
    return <Navigate to="/" replace />
  }

  async function onSubmit(values: FormValues) {
    setError(null)
    try {
      await login(values.email, values.password)
      navigate("/", { replace: true })
    } catch (err) {
      // 401 traz "E-mail ou senha inválidos." da API; 429 traz o aviso de bloqueio; sem resposta,
      // avisa que o servidor está inacessível — antes tudo virava "senha inválida".
      setError(getApiErrorMessage(err, "Não foi possível entrar. Tente novamente."))
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <LoginVisual />

      <div className="flex items-center justify-center bg-background px-4 py-12">
        <div className="animate-nexfi-fade-in-up w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center gap-3 text-center lg:hidden">
            <svg viewBox="0 0 64 64" className="h-12 w-12">
              <defs>
                <linearGradient id="login-g" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="#14BBA6" />
                  <stop offset="1" stopColor="#5EEEA4" />
                </linearGradient>
              </defs>
              <rect width="64" height="64" rx="14" fill="#0B0F19" />
              <path
                d="M16 46 L27 18 L32 18 L24 40 L40 40 L48 18 L48 46 L43 46 L43 26 L36 46 L30 46 L38 24 L32 40 L23 40 Z"
                fill="url(#login-g)"
              />
            </svg>
          </div>

          <div className="mb-8">
            <h1 className="font-heading text-2xl font-semibold">Bem-vindo de volta</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Entre com sua conta para acessar o NexFi.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">E-mail</Label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="voce@exemplo.com"
                  className="pl-9"
                  {...register("email")}
                />
              </div>
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="pl-9"
                  {...register("password")}
                />
              </div>
              {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <Button type="submit" disabled={isSubmitting} className="mt-2 h-11">
              {isSubmitting ? "Entrando…" : "Entrar"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
