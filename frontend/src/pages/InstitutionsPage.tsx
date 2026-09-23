import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { institutionsApi } from "@/api/institutions"
import { InstitutionFormDialog } from "@/components/forms/InstitutionFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useToast } from "@/components/ui/toaster"
import { useInstitutions } from "@/hooks/useReferenceData"
import type { Institution } from "@/types"

export function InstitutionsPage() {
  const { data, isLoading } = useInstitutions()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Institution | null>(null)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const deactivateMutation = useMutation({
    mutationFn: institutionsApi.deactivate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institutions"] })
      notify({ title: "Instituição inativada.", variant: "success" })
    },
  })

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Instituições financeiras</h1>
          <p className="text-sm text-muted-foreground">Bancos, corretoras e carteiras digitais</p>
        </div>
        <Button
          onClick={() => {
            setEditing(null)
            setDialogOpen(true)
          }}
        >
          <Plus className="h-4 w-4" /> Nova instituição
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-card">
        {isLoading ? (
          <div className="p-4">
            <Skeleton className="h-40 w-full" />
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-10 text-center text-sm text-muted-foreground">Nenhuma instituição cadastrada.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Nome curto</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-24" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((inst) => (
                <TableRow key={inst.id}>
                  <TableCell className="font-medium">{inst.name}</TableCell>
                  <TableCell className="text-muted-foreground">{inst.short_name ?? "—"}</TableCell>
                  <TableCell>
                    <Badge variant={inst.active ? "success" : "secondary"}>{inst.active ? "Ativa" : "Inativa"}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setEditing(inst)
                          setDialogOpen(true)
                        }}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      {inst.active && (
                        <button
                          onClick={() => deactivateMutation.mutate(inst.id)}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <InstitutionFormDialog open={dialogOpen} onOpenChange={setDialogOpen} institution={editing} />
    </div>
  )
}
