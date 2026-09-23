import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { useEffect } from "react"
import { cardsApi } from "@/api/cards"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/toaster"
import { flattenCategories, useCategories } from "@/hooks/useReferenceData"
import { todayISO } from "@/lib/format"
import { getApiErrorMessage } from "@/lib/api-error"
import { invalidateFinancialData } from "@/lib/invalidate"

const schema = z.object({
  description: z.string().min(1, "Informe a descrição."),
  total_amount: z.coerce.number().positive("O valor deve ser maior que zero."),
  installments_total: z.coerce.number().min(1).max(60),
  purchase_date: z.string().min(1),
  category_id: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function PurchaseFormDialog({
  open,
  onOpenChange,
  cardId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  cardId: string | null
}) {
  const { data: categories } = useCategories()
  const flatCategories = flattenCategories(categories ?? []).filter((c) => c.kind !== "RECEITA")
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { purchase_date: todayISO(), installments_total: 1 },
  })

  // Reseta ao abrir: sem isso, valores digitados e cancelados reapareciam na próxima abertura
  // (ex.: o saldo informado para a conta A aparecendo no ajuste da conta B).
  useEffect(() => {
    if (open) reset()
  }, [open, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      cardsApi.createPurchase(cardId!, { ...values, category_id: values.category_id || null }),
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Compra registrada.", variant: "success" })
      reset()
      onOpenChange(false)
    },
    onError: (err: unknown) => {
      const message = getApiErrorMessage(err, "Não foi possível registrar a compra.")
      notify({ title: message, variant: "error" })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nova compra no cartão</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="description">Descrição</Label>
            <Input id="description" {...register("description")} placeholder="Ex.: Notebook" />
            {errors.description && <p className="text-xs text-destructive">{errors.description.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="total_amount">Valor total</Label>
              <Input id="total_amount" type="number" step="0.01" {...register("total_amount")} />
              {errors.total_amount && <p className="text-xs text-destructive">{errors.total_amount.message}</p>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="installments_total">Parcelas</Label>
              <Input id="installments_total" type="number" min={1} max={60} {...register("installments_total")} />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="purchase_date">Data da compra</Label>
            <Input id="purchase_date" type="date" {...register("purchase_date")} />
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
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              Registrar compra
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
