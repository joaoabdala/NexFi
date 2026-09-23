import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { cardsApi } from "@/api/cards"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/toaster"
import { useAccounts, useInstitutions } from "@/hooks/useReferenceData"
import type { CreditCard } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"

const schema = z.object({
  institution_id: z.string().min(1, "Selecione a instituição."),
  name: z.string().min(1, "Informe o nome."),
  brand: z.string().optional(),
  last_digits: z.string().max(4).optional(),
  credit_limit: z.coerce.number().positive("Informe um limite válido."),
  closing_day: z.coerce.number().min(1).max(31),
  due_day: z.coerce.number().min(1).max(31),
  default_payment_account_id: z.string().min(1, "Selecione a conta de pagamento padrão."),
})

type FormValues = z.infer<typeof schema>

export function CardFormDialog({
  open,
  onOpenChange,
  card,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  card?: CreditCard | null
}) {
  const { data: institutions } = useInstitutions()
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
        institution_id: card?.institution_id ?? "",
        name: card?.name ?? "",
        brand: card?.brand ?? "",
        last_digits: card?.last_digits ?? "",
        credit_limit: card ? Number(card.credit_limit) : undefined,
        closing_day: card?.closing_day ?? 1,
        due_day: card?.due_day ?? 10,
        default_payment_account_id: card?.default_payment_account_id ?? "",
      })
    }
  }, [open, card, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) => (card ? cardsApi.update(card.id, values) : cardsApi.create(values)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cards"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      notify({ title: "Cartão salvo.", variant: "success" })
      onOpenChange(false)
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível salvar o cartão."), variant: "error" }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{card ? "Editar cartão" : "Novo cartão"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
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

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Nome</Label>
              <Input id="name" {...register("name")} placeholder="Ex.: Nubank Cartão" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="brand">Bandeira</Label>
              <Input id="brand" {...register("brand")} placeholder="Ex.: Mastercard" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="last_digits">Últimos 4 dígitos</Label>
              <Input id="last_digits" {...register("last_digits")} maxLength={4} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="closing_day">Fechamento</Label>
              <Input id="closing_day" type="number" min={1} max={31} {...register("closing_day")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="due_day">Vencimento</Label>
              <Input id="due_day" type="number" min={1} max={31} {...register("due_day")} />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="credit_limit">Limite</Label>
            <Input id="credit_limit" type="number" step="0.01" {...register("credit_limit")} />
            {errors.credit_limit && <p className="text-xs text-destructive">{errors.credit_limit.message}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Conta de pagamento padrão</Label>
            <Controller
              control={control}
              name="default_payment_account_id"
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
            {errors.default_payment_account_id && (
              <p className="text-xs text-destructive">{errors.default_payment_account_id.message}</p>
            )}
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
