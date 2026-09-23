import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { useEffect } from "react"
import { transfersApi } from "@/api/transfers"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/toaster"
import { useAccounts } from "@/hooks/useReferenceData"
import { todayISO } from "@/lib/format"
import { getApiErrorMessage } from "@/lib/api-error"
import { invalidateFinancialData } from "@/lib/invalidate"

const schema = z
  .object({
    from_account_id: z.string().min(1, "Selecione a conta de origem."),
    to_account_id: z.string().min(1, "Selecione a conta de destino."),
    amount: z.coerce.number().positive("O valor deve ser maior que zero."),
    date: z.string().min(1),
    description: z.string().optional(),
  })
  .refine((v) => v.from_account_id !== v.to_account_id, {
    message: "A conta de origem deve ser diferente da conta de destino.",
    path: ["to_account_id"],
  })

type FormValues = z.infer<typeof schema>

export function TransferFormDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const { data: accounts } = useAccounts()
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
    defaultValues: { date: todayISO() },
  })

  // Reseta ao abrir: sem isso, valores digitados e cancelados reapareciam na próxima abertura
  // (ex.: o saldo informado para a conta A aparecendo no ajuste da conta B).
  useEffect(() => {
    if (open) reset()
  }, [open, reset])

  const mutation = useMutation({
    mutationFn: transfersApi.create,
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Transferência realizada.", variant: "success" })
      reset()
      onOpenChange(false)
    },
    onError: (err: unknown) => {
      const message = getApiErrorMessage(err, "Não foi possível realizar a transferência.")
      notify({ title: message, variant: "error" })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Transferência entre contas</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Conta de origem</Label>
            <Controller
              control={control}
              name="from_account_id"
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
            {errors.from_account_id && <p className="text-xs text-destructive">{errors.from_account_id.message}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Conta de destino</Label>
            <Controller
              control={control}
              name="to_account_id"
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
            {errors.to_account_id && <p className="text-xs text-destructive">{errors.to_account_id.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="amount">Valor</Label>
              <Input id="amount" type="number" step="0.01" {...register("amount")} />
              {errors.amount && <p className="text-xs text-destructive">{errors.amount.message}</p>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="date">Data</Label>
              <Input id="date" type="date" {...register("date")} />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="description">Descrição (opcional)</Label>
            <Input id="description" {...register("description")} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              Transferir
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
