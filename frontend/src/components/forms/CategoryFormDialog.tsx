import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { categoriesApi } from "@/api/categories"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/toaster"
import { useCategories } from "@/hooks/useReferenceData"
import type { Category } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"

const schema = z.object({
  name: z.string().min(1, "Informe o nome."),
  kind: z.enum(["RECEITA", "DESPESA", "AMBOS"]),
  parent_id: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function CategoryFormDialog({
  open,
  onOpenChange,
  category,
  defaultParentId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  category?: Category | null
  defaultParentId?: string | null
}) {
  const { data: categories } = useCategories()
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
        name: category?.name ?? "",
        kind: category?.kind ?? "DESPESA",
        parent_id: category?.parent_id ?? defaultParentId ?? "",
      })
    }
  }, [open, category, defaultParentId, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload = { ...values, parent_id: values.parent_id || null }
      return category ? categoriesApi.update(category.id, payload) : categoriesApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
      notify({ title: "Categoria salva.", variant: "success" })
      onOpenChange(false)
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível salvar a categoria."), variant: "error" }),
  })

  const topLevelCategories = (categories ?? []).filter((c) => !c.parent_id && c.id !== category?.id)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{category ? "Editar categoria" : "Nova categoria"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Nome</Label>
            <Input id="name" {...register("name")} placeholder="Ex.: Alimentação" />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Tipo</Label>
            <Controller
              control={control}
              name="kind"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DESPESA">Despesa</SelectItem>
                    <SelectItem value="RECEITA">Receita</SelectItem>
                    <SelectItem value="AMBOS">Ambos</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Categoria pai (opcional — cria subcategoria)</Label>
            <Controller
              control={control}
              name="parent_id"
              render={({ field }) => (
                // Mover uma categoria para outro pai não é suportado pela API (o campo era
                // ignorado em silêncio): bloqueado na edição.
                <Select
                  value={field.value || "none"}
                  onValueChange={(v) => field.onChange(v === "none" ? "" : v)}
                  disabled={!!category}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Categoria principal" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Categoria principal (sem pai)</SelectItem>
                    {topLevelCategories.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.name}
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
              Salvar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
