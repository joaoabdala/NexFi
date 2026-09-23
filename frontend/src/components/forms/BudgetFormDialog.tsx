import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { useEffect } from "react"
import { budgetsApi } from "@/api/planning"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/components/ui/toaster"
import { flattenCategories, useCategories } from "@/hooks/useReferenceData"
import { getApiErrorMessage } from "@/lib/api-error"
import { optionalNumber } from "@/lib/zod-helpers"

const schema = z.object({
  category_id: z.string().min(1, "Selecione a categoria."),
  amount: z.coerce.number().positive("Informe um valor válido."),
  specific_month: z.boolean(),
  month: optionalNumber(z.coerce.number().min(1).max(12)),
  year: optionalNumber(z.coerce.number().min(2000).max(2100)),
})

type FormValues = z.infer<typeof schema>

export function BudgetFormDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const { data: categories } = useCategories()
  const flatCategories = flattenCategories(categories ?? []).filter((c) => c.kind !== "RECEITA")
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
    defaultValues: {
      specific_month: false,
      month: new Date().getMonth() + 1,
      year: new Date().getFullYear(),
    },
  })

  // Reseta ao abrir: sem isso, valores digitados e cancelados reapareciam na próxima abertura
  // (ex.: o saldo informado para a conta A aparecendo no ajuste da conta B).
  useEffect(() => {
    if (open) reset()
  }, [open, reset])

  const specificMonth = watch("specific_month")

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      budgetsApi.create({
        category_id: values.category_id,
        amount: values.amount,
        month: values.specific_month ? values.month : null,
        year: values.specific_month ? values.year : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] })
      queryClient.invalidateQueries({ queryKey: ["budgets-summary"] })
      notify({ title: "Orçamento salvo.", variant: "success" })
      reset()
      onOpenChange(false)
    },
    onError: (err: unknown) => {
      const message = getApiErrorMessage(err, "Não foi possível salvar o orçamento.")
      notify({ title: message, variant: "error" })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Novo orçamento</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Categoria</Label>
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
            {errors.category_id && <p className="text-xs text-destructive">{errors.category_id.message}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="amount">Valor do orçamento</Label>
            <Input id="amount" type="number" step="0.01" {...register("amount")} />
            {errors.amount && <p className="text-xs text-destructive">{errors.amount.message}</p>}
          </div>

          <div className="flex items-center justify-between rounded-md border border-border p-3">
            <div>
              <p className="text-sm font-medium">Específico de um mês</p>
              <p className="text-xs text-muted-foreground">Desligado = orçamento padrão recorrente</p>
            </div>
            <Controller
              control={control}
              name="specific_month"
              render={({ field }) => <Switch checked={field.value} onCheckedChange={field.onChange} />}
            />
          </div>

          {specificMonth && (
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="month">Mês</Label>
                <Input id="month" type="number" min={1} max={12} {...register("month")} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="year">Ano</Label>
                <Input id="year" type="number" {...register("year")} />
              </div>
            </div>
          )}

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
