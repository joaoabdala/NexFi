import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { accountsApi } from "@/api/accounts"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/toaster"
import { useInstitutions } from "@/hooks/useReferenceData"
import { todayISO } from "@/lib/format"
import type { Account, AccountType } from "@/types"

const ACCOUNT_TYPES: { value: AccountType; label: string }[] = [
  { value: "CONTA_CORRENTE", label: "Conta corrente" },
  { value: "CONTA_DIGITAL", label: "Conta digital" },
  { value: "POUPANCA", label: "Poupança" },
  { value: "DINHEIRO", label: "Dinheiro" },
  { value: "COFRINHO_RESERVA", label: "Cofrinho / Reserva" },
  { value: "INVESTIMENTO", label: "Investimento" },
  { value: "OUTROS", label: "Outros" },
]

const schema = z.object({
  institution_id: z.string().min(1, "Selecione a instituição."),
  name: z.string().min(1, "Informe o nome."),
  type: z.enum(["CONTA_CORRENTE", "CONTA_DIGITAL", "POUPANCA", "DINHEIRO", "COFRINHO_RESERVA", "INVESTIMENTO", "OUTROS"]),
  initial_balance: z.coerce.number(),
  initial_balance_date: z.string().min(1),
  include_in_available_worth: z.boolean(),
  include_in_invested_worth: z.boolean(),
  note: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function AccountFormDialog({
  open,
  onOpenChange,
  account,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  account?: Account | null
}) {
  const { data: institutions } = useInstitutions()
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  useEffect(() => {
    if (open) {
      reset({
        institution_id: account?.institution_id ?? "",
        name: account?.name ?? "",
        type: account?.type ?? "CONTA_CORRENTE",
        initial_balance: account ? Number(account.initial_balance) : 0,
        initial_balance_date: account?.initial_balance_date ?? todayISO(),
        include_in_available_worth: account?.include_in_available_worth ?? true,
        include_in_invested_worth: account?.include_in_invested_worth ?? false,
        note: account?.note ?? "",
      })
    }
  }, [open, account, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      account
        ? accountsApi.update(account.id, values)
        : accountsApi.create(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      notify({ title: "Conta salva.", variant: "success" })
      onOpenChange(false)
    },
    onError: () => notify({ title: "Não foi possível salvar a conta.", variant: "error" }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{account ? "Editar conta" : "Nova conta"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Instituição</Label>
            <Controller
              control={control}
              name="institution_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {institutions?.map((i) => (
                      <SelectItem key={i.id} value={i.id}>
                        {i.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.institution_id && <p className="text-xs text-destructive">{errors.institution_id.message}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Nome</Label>
            <Input id="name" {...register("name")} placeholder="Ex.: Saldo" />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Tipo</Label>
            <Controller
              control={control}
              name="type"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ACCOUNT_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="initial_balance">Saldo inicial</Label>
              <Input id="initial_balance" type="number" step="0.01" {...register("initial_balance")} disabled={!!account} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="initial_balance_date">Data do saldo inicial</Label>
              <Input id="initial_balance_date" type="date" {...register("initial_balance_date")} disabled={!!account} />
            </div>
          </div>
          {account && (
            <p className="text-xs text-muted-foreground">
              Saldo inicial não pode ser alterado após a criação — use um ajuste de saldo se necessário.
            </p>
          )}

          <div className="flex items-center justify-between rounded-md border border-border p-3">
            <div>
              <p className="text-sm font-medium">Incluir no patrimônio disponível</p>
            </div>
            <Controller
              control={control}
              name="include_in_available_worth"
              render={({ field }) => <Switch checked={field.value} onCheckedChange={field.onChange} />}
            />
          </div>
          <div className="flex items-center justify-between rounded-md border border-border p-3">
            <div>
              <p className="text-sm font-medium">Incluir no patrimônio investido</p>
            </div>
            <Controller
              control={control}
              name="include_in_invested_worth"
              render={({ field }) => <Switch checked={field.value} onCheckedChange={field.onChange} />}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="note">Observação</Label>
            <Textarea id="note" {...register("note")} />
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
