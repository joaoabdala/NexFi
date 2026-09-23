import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { amortizationsApi, financingApi } from "@/api/financing"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/toaster"
import { useAccounts } from "@/hooks/useReferenceData"
import { formatCurrency, todayISO } from "@/lib/format"
import { getApiErrorMessage } from "@/lib/api-error"

const schema = z.object({
  date: z.string().min(1),
  paid_amount: z.coerce.number().positive("Informe o valor pago."),
  type: z.enum(["REDUCAO_PRAZO", "REDUCAO_PARCELA"]),
  account_id: z.string().min(1, "Selecione a conta."),
  installment_numbers: z.array(z.number()).optional(),
  note: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function AmortizationFormDialog({
  open,
  onOpenChange,
  commitmentId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  commitmentId: string | null
}) {
  const { data: accounts } = useAccounts()
  const { data: installments } = useQuery({
    queryKey: ["financing-installments", commitmentId],
    queryFn: () => financingApi.listInstallments(commitmentId!),
    enabled: open && !!commitmentId,
  })
  const pendingInstallments = (installments ?? []).filter((i) => i.status === "PENDENTE")

  const queryClient = useQueryClient()
  const { notify } = useToast()

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { date: todayISO(), type: "REDUCAO_PRAZO", installment_numbers: [] },
  })

  const type = watch("type")
  const selectedNumbers = watch("installment_numbers") ?? []

  function toggleNumber(n: number) {
    const current = selectedNumbers.includes(n)
      ? selectedNumbers.filter((x) => x !== n)
      : [...selectedNumbers, n]
    setValue("installment_numbers", current)
  }

  const mutation = useMutation({
    mutationFn: (values: FormValues) => amortizationsApi.create(commitmentId!, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financing"] })
      queryClient.invalidateQueries({ queryKey: ["financing-installments"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      notify({ title: "Amortização registrada.", variant: "success" })
      onOpenChange(false)
    },
    onError: (err: unknown) => {
      const message = getApiErrorMessage(err, "Não foi possível registrar a amortização.")
      notify({ title: message, variant: "error" })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Amortização extraordinária</DialogTitle>
          <DialogDescription>
            Reduza o prazo (elimina parcelas futuras) ou o valor das parcelas restantes.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="date">Data</Label>
              <Input id="date" type="date" {...register("date")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="paid_amount">Valor efetivamente pago</Label>
              <Input id="paid_amount" type="number" step="0.01" {...register("paid_amount")} />
              {errors.paid_amount && <p className="text-xs text-destructive">{errors.paid_amount.message}</p>}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Tipo de amortização</Label>
            <Controller
              control={control}
              name="type"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="REDUCAO_PRAZO">Redução de prazo (elimina parcelas)</SelectItem>
                    <SelectItem value="REDUCAO_PARCELA">Redução de parcela (reduz valor restante)</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Conta utilizada</Label>
            <Controller
              control={control}
              name="account_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts?.map((a) => (
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

          {type === "REDUCAO_PRAZO" && (
            <div className="flex flex-col gap-1.5">
              <Label>Parcelas a eliminar (selecione as últimas parcelas pendentes)</Label>
              <div className="grid max-h-40 grid-cols-4 gap-2 overflow-y-auto rounded-md border border-border p-2 scrollbar-thin">
                {pendingInstallments.map((installment) => (
                  <label key={installment.id} className="flex items-center gap-1.5 text-xs">
                    <Checkbox
                      checked={selectedNumbers.includes(installment.number)}
                      onCheckedChange={() => toggleNumber(installment.number)}
                    />
                    {installment.number} ({formatCurrency(installment.updated_amount)})
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="note">Observação</Label>
            <Textarea id="note" {...register("note")} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              Confirmar amortização
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
