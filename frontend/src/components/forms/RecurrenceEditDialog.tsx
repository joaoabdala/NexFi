import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { recurrencesApi } from "@/api/planning"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/components/ui/toaster"
import { flattenCategories, useAccounts, useCategories } from "@/hooks/useReferenceData"
import { formatDate } from "@/lib/format"
import type { RecurrenceRule } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"
import { invalidateFinancialData } from "@/lib/invalidate"

const schema = z.object({
  description: z.string().min(1, "Informe a descrição."),
  amount: z.coerce.number().positive("Informe um valor válido."),
  category_id: z.string().optional(),
  end_date: z.string().optional(),
  active: z.boolean(),
})

type FormValues = z.infer<typeof schema>

const FREQUENCY_LABEL: Record<string, string> = {
  SEMANAL: "Semanal",
  MENSAL: "Mensal",
  ANUAL: "Anual",
  PERSONALIZADA: "Personalizada",
}

export function RecurrenceEditDialog({
  open,
  onOpenChange,
  rule,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  rule: RecurrenceRule | null
}) {
  const { data: accounts } = useAccounts()
  const { data: categories } = useCategories()
  const flatCategories = flattenCategories(categories ?? [])
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
    if (open && rule) {
      reset({
        description: rule.description,
        amount: Number(rule.amount),
        category_id: rule.category_id ?? "",
        end_date: rule.end_date ?? "",
        active: rule.active,
      })
    }
  }, [open, rule, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      recurrencesApi.update(rule!.id, { ...values, category_id: values.category_id || null, end_date: values.end_date || null }),
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Recorrência atualizada.", variant: "success" })
      onOpenChange(false)
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível atualizar a recorrência."), variant: "error" }),
  })

  if (!rule) return null

  const account = accounts?.find((a) => a.id === rule.account_id)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Editar recorrência</DialogTitle>
          <DialogDescription>
            Tipo, conta, frequência e data de início não podem ser alterados após a criação —
            transações futuras já podem ter sido geradas com essas configurações. Para mudá-los,
            inative esta recorrência e crie uma nova.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-2 rounded-md border border-border bg-secondary/40 p-3 text-xs text-muted-foreground">
          <span>Tipo: {rule.type === "RECEITA" ? "Receita" : "Despesa"}</span>
          <span>Frequência: {FREQUENCY_LABEL[rule.frequency]}</span>
          <span>Conta: {account ? `${account.institution_name} — ${account.name}` : "—"}</span>
          <span>Início: {formatDate(rule.start_date)}</span>
        </div>

        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="description">Descrição</Label>
            <Input id="description" {...register("description")} />
            {errors.description && <p className="text-xs text-destructive">{errors.description.message}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="amount">Valor</Label>
            <Input id="amount" type="number" step="0.01" {...register("amount")} />
            {errors.amount && <p className="text-xs text-destructive">{errors.amount.message}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Categoria (opcional)</Label>
            <Controller
              control={control}
              name="category_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {flatCategories.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="end_date">Término (opcional)</Label>
            <Input id="end_date" type="date" {...register("end_date")} />
          </div>

          <div className="flex items-center justify-between rounded-md border border-border p-3">
            <div>
              <p className="text-sm font-medium">Recorrência ativa</p>
              <p className="text-xs text-muted-foreground">
                Inativa não gera novas transações futuras
              </p>
            </div>
            <Controller
              control={control}
              name="active"
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
