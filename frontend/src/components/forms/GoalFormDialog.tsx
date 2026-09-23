import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { goalsApi } from "@/api/planning"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/toaster"
import { useAccounts } from "@/hooks/useReferenceData"
import type { FinancialGoal } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"

const schema = z.object({
  name: z.string().min(1, "Informe o nome."),
  target_amount: z.coerce.number().positive("Informe o valor alvo."),
  current_amount: z.coerce.number().optional(),
  linked_account_id: z.string().optional(),
  target_date: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function GoalFormDialog({
  open,
  onOpenChange,
  goal,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  goal?: FinancialGoal | null
}) {
  const { data: accounts } = useAccounts()
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
        name: goal?.name ?? "",
        target_amount: goal ? Number(goal.target_amount) : undefined,
        current_amount: goal ? Number(goal.current_amount) : 0,
        linked_account_id: goal?.linked_account_id ?? "",
        target_date: goal?.target_date ?? "",
      })
    }
  }, [open, goal, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload = { ...values, linked_account_id: values.linked_account_id || null, target_date: values.target_date || null }
      return goal ? goalsApi.update(goal.id, payload) : goalsApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] })
      notify({ title: "Meta salva.", variant: "success" })
      onOpenChange(false)
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível salvar a meta."), variant: "error" }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{goal ? "Editar meta" : "Nova meta"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Nome</Label>
            <Input id="name" {...register("name")} placeholder="Ex.: Reserva de emergência" />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="target_amount">Valor alvo</Label>
            <Input id="target_amount" type="number" step="0.01" {...register("target_amount")} />
            {errors.target_amount && <p className="text-xs text-destructive">{errors.target_amount.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Conta vinculada (opcional — usa o saldo da conta como progresso)</Label>
            <Controller
              control={control}
              name="linked_account_id"
              render={({ field }) => (
                <Select value={field.value || "none"} onValueChange={(v) => field.onChange(v === "none" ? "" : v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Nenhuma" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Nenhuma (valor manual)</SelectItem>
                    {accounts?.map((a) => (
                      <SelectItem key={a.id} value={a.id}>
                        {a.institution_name} — {a.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="current_amount">Valor atual (se não vinculado a uma conta)</Label>
            <Input id="current_amount" type="number" step="0.01" {...register("current_amount")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="target_date">Data alvo (opcional)</Label>
            <Input id="target_date" type="date" {...register("target_date")} />
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
