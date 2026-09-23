import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { institutionsApi } from "@/api/institutions"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/toaster"
import type { Institution } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"

const schema = z.object({
  name: z.string().min(1, "Informe o nome."),
  short_name: z.string().optional(),
  note: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function InstitutionFormDialog({
  open,
  onOpenChange,
  institution,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  institution?: Institution | null
}) {
  const queryClient = useQueryClient()
  const { notify } = useToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  useEffect(() => {
    if (open) {
      reset({
        name: institution?.name ?? "",
        short_name: institution?.short_name ?? "",
        note: institution?.note ?? "",
      })
    }
  }, [open, institution, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      institution ? institutionsApi.update(institution.id, values) : institutionsApi.create(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institutions"] })
      notify({ title: "Instituição salva.", variant: "success" })
      onOpenChange(false)
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível salvar a instituição."), variant: "error" }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{institution ? "Editar instituição" : "Nova instituição"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutateAsync(v).catch(() => {}))} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Nome</Label>
            <Input id="name" {...register("name")} placeholder="Ex.: Nubank" />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="short_name">Nome curto</Label>
            <Input id="short_name" {...register("short_name")} placeholder="Ex.: Nu" />
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
              Salvar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
