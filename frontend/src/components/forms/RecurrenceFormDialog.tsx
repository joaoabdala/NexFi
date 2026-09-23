import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { recurrencesApi } from "@/api/planning"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/toaster"
import { flattenCategories, useAccounts, useCategories } from "@/hooks/useReferenceData"
import { todayISO } from "@/lib/format"
import { getApiErrorMessage } from "@/lib/api-error"
import { invalidateFinancialData } from "@/lib/invalidate"
import { optionalNumber } from "@/lib/zod-helpers"

const schema = z.object({
  description: z.string().min(1, "Informe a descrição."),
  type: z.enum(["RECEITA", "DESPESA"]),
  amount: z.coerce.number().positive("Informe um valor válido."),
  account_id: z.string().min(1, "Selecione a conta."),
  category_id: z.string().optional(),
  frequency: z.enum(["SEMANAL", "MENSAL", "ANUAL", "PERSONALIZADA"]),
  reference_day: optionalNumber(z.coerce.number().min(1).max(31)),
  custom_interval_days: optionalNumber(z.coerce.number().min(1)),
  start_date: z.string().min(1),
  end_date: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function RecurrenceFormDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const { data: accounts } = useAccounts()
  const { data: categories } = useCategories()
  const flatCategories = flattenCategories(categories ?? [])
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const {
    register,
    control,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { type: "DESPESA", frequency: "MENSAL", start_date: todayISO() },
  })

  const frequency = watch("frequency")

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      recurrencesApi.create({ ...values, category_id: values.category_id || null, end_date: values.end_date || null }),
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Recorrência criada.", variant: "success" })
      reset()
      onOpenChange(false)
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível criar a recorrência."), variant: "error" }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nova recorrência</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="description">Descrição</Label>
            <Input id="description" {...register("description")} placeholder="Ex.: Netflix" />
            {errors.description && <p className="text-xs text-destructive">{errors.description.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
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
                      <SelectItem value="DESPESA">Despesa</SelectItem>
                      <SelectItem value="RECEITA">Receita</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="amount">Valor</Label>
              <Input id="amount" type="number" step="0.01" {...register("amount")} />
              {errors.amount && <p className="text-xs text-destructive">{errors.amount.message}</p>}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Conta</Label>
            <Controller
              control={control}
              name="account_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts?.filter((a) => a.active).map((a) => (
                      <SelectItem key={a.id} value={a.id}>
                        {a.institution_name} — {a.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.account_id && <p className="text-xs text-destructive">{errors.account_id.message}</p>}
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

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label>Frequência</Label>
              <Controller
                control={control}
                name="frequency"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="SEMANAL">Semanal</SelectItem>
                      <SelectItem value="MENSAL">Mensal</SelectItem>
                      <SelectItem value="ANUAL">Anual</SelectItem>
                      <SelectItem value="PERSONALIZADA">Personalizada</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            {frequency === "PERSONALIZADA" ? (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="custom_interval_days">A cada (dias)</Label>
                <Input id="custom_interval_days" type="number" min={1} {...register("custom_interval_days")} />
              </div>
            ) : (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="reference_day">Dia de referência</Label>
                <Input id="reference_day" type="number" min={1} max={31} {...register("reference_day")} />
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="start_date">Início</Label>
              <Input id="start_date" type="date" {...register("start_date")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="end_date">Término (opcional)</Label>
              <Input id="end_date" type="date" {...register("end_date")} />
            </div>
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
