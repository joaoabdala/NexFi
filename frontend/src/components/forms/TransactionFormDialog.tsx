import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ChevronDown } from "lucide-react"
import { useEffect, useState } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { transactionsApi } from "@/api/transactions"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/toaster"
import { flattenCategories, useAccounts, useCategories } from "@/hooks/useReferenceData"
import { todayISO } from "@/lib/format"
import { getApiErrorMessage } from "@/lib/api-error"
import { invalidateFinancialData } from "@/lib/invalidate"

const schema = z.object({
  type: z.enum(["RECEITA", "DESPESA", "RENDIMENTO"]),
  description: z.string().min(1, "Informe uma descrição."),
  amount: z.coerce.number().positive("O valor deve ser maior que zero."),
  account_id: z.string().min(1, "Selecione a conta."),
  category_id: z.string().min(1, "Selecione a categoria."),
  competence_date: z.string().min(1),
  payment_date: z.string().optional(),
  status: z.enum(["PENDENTE", "CONFIRMADA"]),
  note: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function TransactionFormDialog({
  open,
  onOpenChange,
  defaultType = "DESPESA",
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  defaultType?: "RECEITA" | "DESPESA" | "RENDIMENTO"
}) {
  const [showMore, setShowMore] = useState(false)
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
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: defaultType,
      competence_date: todayISO(),
      payment_date: todayISO(),
      status: "CONFIRMADA",
    },
  })

  useEffect(() => {
    if (open) {
      reset({
        type: defaultType,
        competence_date: todayISO(),
        payment_date: todayISO(),
        status: "CONFIRMADA",
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, defaultType])

  const type = watch("type")
  const categoryOptions = flatCategories.filter(
    (c) => c.kind === "AMBOS" || c.kind === (type === "DESPESA" ? "DESPESA" : "RECEITA"),
  )
  // Ao trocar despesa ↔ receita, a categoria escolhida antes pode não servir mais; mantê-la
  // selecionada (e escondida da lista) fazia a API recusar o envio.
  const categoryId = watch("category_id")
  useEffect(() => {
    if (categoryId && !categoryOptions.some((c) => c.id === categoryId)) setValue("category_id", "")
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type])

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      transactionsApi.create({
        ...values,
        payment_date: values.status === "CONFIRMADA" ? values.payment_date || todayISO() : null,
      }),
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Movimentação registrada.", variant: "success" })
      reset()
      onOpenChange(false)
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível salvar a movimentação."), variant: "error" }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nova movimentação</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="grid grid-cols-3 gap-2">
            {(["RECEITA", "DESPESA", "RENDIMENTO"] as const).map((t) => (
              <label
                key={t}
                className={`flex cursor-pointer items-center justify-center rounded-md border px-2 py-2 text-sm font-medium ${
                  type === t ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground"
                }`}
              >
                <input type="radio" value={t} {...register("type")} className="sr-only" />
                {t === "RECEITA" ? "Receita" : t === "DESPESA" ? "Despesa" : "Rendimento"}
              </label>
            ))}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="description">Descrição</Label>
            <Input id="description" {...register("description")} placeholder="Ex.: Supermercado" />
            {errors.description && <p className="text-xs text-destructive">{errors.description.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="amount">Valor</Label>
              <Input id="amount" type="number" step="0.01" {...register("amount")} placeholder="0,00" />
              {errors.amount && <p className="text-xs text-destructive">{errors.amount.message}</p>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="competence_date">Data</Label>
              <Input id="competence_date" type="date" {...register("competence_date")} />
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
                    <SelectValue placeholder="Selecione a conta" />
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
            <Label>Categoria</Label>
            <Controller
              control={control}
              name="category_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione a categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    {categoryOptions.map((c) => (
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

          <button
            type="button"
            onClick={() => setShowMore((v) => !v)}
            className="flex items-center gap-1 self-start text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showMore ? "rotate-180" : ""}`} />
            Mais opções
          </button>

          {showMore && (
            <div className="flex flex-col gap-3 rounded-md border border-border p-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <Label>Status</Label>
                  <Controller
                    control={control}
                    name="status"
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="CONFIRMADA">Confirmada</SelectItem>
                          <SelectItem value="PENDENTE">Pendente</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="payment_date">Data de pagamento</Label>
                  <Input id="payment_date" type="date" {...register("payment_date")} />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="note">Observação</Label>
                <Textarea id="note" {...register("note")} />
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
