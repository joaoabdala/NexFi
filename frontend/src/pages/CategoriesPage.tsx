import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { categoriesApi } from "@/api/categories"
import { CategoryFormDialog } from "@/components/forms/CategoryFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toaster"
import { useCategories } from "@/hooks/useReferenceData"
import type { Category } from "@/types"

const KIND_LABEL: Record<string, string> = { RECEITA: "Receita", DESPESA: "Despesa", AMBOS: "Ambos" }

export function CategoriesPage() {
  const { data, isLoading } = useCategories()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Category | null>(null)
  const [parentFor, setParentFor] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const deactivateMutation = useMutation({
    mutationFn: categoriesApi.deactivate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
      notify({ title: "Categoria inativada.", variant: "success" })
    },
  })

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Categorias</h1>
          <p className="text-sm text-muted-foreground">Organize receitas e despesas em categorias e subcategorias</p>
        </div>
        <Button
          onClick={() => {
            setEditing(null)
            setParentFor(null)
            setDialogOpen(true)
          }}
        >
          <Plus className="h-4 w-4" /> Nova categoria
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : !data || data.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-10 text-center text-sm text-muted-foreground">
          Nenhuma categoria cadastrada.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {data.map((parent) => (
            <div key={parent.id} className="rounded-lg border border-border bg-card p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <p className="font-medium">{parent.name}</p>
                  <Badge variant="outline">{KIND_LABEL[parent.kind]}</Badge>
                  {!parent.active && <Badge variant="secondary">Inativa</Badge>}
                </div>
                <div className="flex gap-3 text-xs">
                  <button
                    onClick={() => {
                      setEditing(null)
                      setParentFor(parent.id)
                      setDialogOpen(true)
                    }}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    + Subcategoria
                  </button>
                  <button
                    onClick={() => {
                      setEditing(parent)
                      setParentFor(null)
                      setDialogOpen(true)
                    }}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  {parent.active && (
                    <button
                      onClick={() => deactivateMutation.mutate(parent.id)}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>
              {parent.children.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2 border-t border-border pt-2">
                  {parent.children.map((child) => (
                    <div
                      key={child.id}
                      className="flex items-center gap-1.5 rounded-full border border-border px-3 py-1 text-xs"
                    >
                      <span>{child.name}</span>
                      <button onClick={() => { setEditing(child); setParentFor(null); setDialogOpen(true) }}>
                        <Pencil className="h-3 w-3 text-muted-foreground" />
                      </button>
                      {child.active && (
                        <button onClick={() => deactivateMutation.mutate(child.id)}>
                          <Trash2 className="h-3 w-3 text-muted-foreground" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <CategoryFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        category={editing}
        defaultParentId={parentFor}
      />
    </div>
  )
}
