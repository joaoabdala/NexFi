import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { useEffect } from "react"
import { financingApi } from "@/api/financing"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/toaster"
import { useInstitutions } from "@/hooks/useReferenceData"
import { todayISO } from "@/lib/format"
import { getApiErrorMessage } from "@/lib/api-error"
import { invalidateFinancialData } from "@/lib/invalidate"
import { optionalNumber } from "@/lib/zod-helpers"

const schema = z.object({
  institution_id: z.string().min(1, "Selecione a instituição."),
  type: z.enum(["FINANCIAMENTO", "EMPRESTIMO", "CONSORCIO", "OUTROS"]),
  name: z.string().min(1, "Informe o nome."),
  asset_value: optionalNumber(z.coerce.number()),
  down_payment: optionalNumber(z.coerce.number()),
  financed_amount: z.coerce.number().positive("Informe o valor financiado."),
  installments_total: z.coerce.number().min(1).max(600),
  default_installment_amount: z.coerce.number().positive("Informe o valor da parcela."),
  start_date: z.string().min(1),
  due_day: z.coerce.number().min(1).max(31),
  note: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function CommitmentFormDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const { data: institutions } = useInstitutions()
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
    defaultValues: { type: "FINANCIAMENTO", start_date: todayISO() },
  })

  // Reseta ao abrir: sem isso, valores digitados e cancelados reapareciam na próxima abertura
  // (ex.: o saldo informado para a conta A aparecendo no ajuste da conta B).
  useEffect(() => {
    if (open) reset()
  }, [open, reset])

  const mutation = useMutation({
    mutationFn: financingApi.create,
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Financiamento cadastrado.", variant: "success" })
      reset()
      onOpenChange(false)
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível cadastrar o financiamento."), variant: "error" }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Novo financiamento</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Nome / descrição</Label>
            <Input id="name" {...register("name")} placeholder="Ex.: Financiamento Apartamento" />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
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
                      <SelectItem value="FINANCIAMENTO">Financiamento</SelectItem>
                      <SelectItem value="EMPRESTIMO">Empréstimo</SelectItem>
                      <SelectItem value="CONSORCIO">Consórcio</SelectItem>
                      <SelectItem value="OUTROS">Outros</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="asset_value">Valor do bem (opcional)</Label>
              <Input id="asset_value" type="number" step="0.01" {...register("asset_value")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="down_payment">Entrada (opcional)</Label>
              <Input id="down_payment" type="number" step="0.01" {...register("down_payment")} />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="financed_amount">Valor financiado</Label>
            <Input id="financed_amount" type="number" step="0.01" {...register("financed_amount")} />
            {errors.financed_amount && <p className="text-xs text-destructive">{errors.financed_amount.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="installments_total">Número de parcelas</Label>
              <Input id="installments_total" type="number" min={1} {...register("installments_total")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="default_installment_amount">Valor da parcela</Label>
              <Input id="default_installment_amount" type="number" step="0.01" {...register("default_installment_amount")} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="start_date">Data inicial</Label>
              <Input id="start_date" type="date" {...register("start_date")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="due_day">Dia de vencimento</Label>
              <Input id="due_day" type="number" min={1} max={31} {...register("due_day")} />
            </div>
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
              Cadastrar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
