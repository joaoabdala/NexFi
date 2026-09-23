import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { accountsApi } from "@/api/accounts"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/toaster"
import { todayISO } from "@/lib/format"
import type { Account } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"

const schema = z.object({
  informed_balance: z.coerce.number(),
  date: z.string().min(1),
  note: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function BalanceAdjustmentDialog({
  open,
  onOpenChange,
  account,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  account: Account | null
}) {
  const queryClient = useQueryClient()
  const { notify } = useToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { date: todayISO() },
  })

  const mutation = useMutation({
    mutationFn: (values: FormValues) => accountsApi.adjustBalance(account!.id, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      notify({ title: "Saldo ajustado.", variant: "success" })
      reset()
      onOpenChange(false)
    },
    onError: (err: unknown) => {
      const message = getApiErrorMessage(err, "Não foi possível ajustar o saldo.")
      notify({ title: message, variant: "error" })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Ajustar saldo — {account?.name}</DialogTitle>
          <DialogDescription>
            Informe o saldo correto conforme o extrato do banco. A diferença será registrada como um
            ajuste auditável — não conta como receita nem despesa.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="informed_balance">Saldo correto</Label>
            <Input id="informed_balance" type="number" step="0.01" {...register("informed_balance")} />
            {errors.informed_balance && <p className="text-xs text-destructive">{errors.informed_balance.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="date">Data</Label>
            <Input id="date" type="date" {...register("date")} />
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
              Ajustar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
