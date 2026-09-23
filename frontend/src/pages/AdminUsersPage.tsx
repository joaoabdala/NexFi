import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { adminUsersApi } from "@/api/admin"
import { AdminUserFormDialog } from "@/components/forms/AdminUserFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useToast } from "@/components/ui/toaster"
import { useAuth } from "@/contexts/AuthContext"
import { formatDate } from "@/lib/format"
import type { AdminUser } from "@/types"

export function AdminUsersPage() {
  const { user: currentUser } = useAuth()
  const { data, isLoading } = useQuery({ queryKey: ["admin-users"], queryFn: adminUsersApi.list })
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<AdminUser | null>(null)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const removeMutation = useMutation({
    mutationFn: adminUsersApi.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      notify({ title: "Usuário excluído.", variant: "success" })
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Não foi possível excluir o usuário."
      notify({ title: message, variant: "error" })
    },
  })

  function handleDelete(target: AdminUser) {
    const confirmed = window.confirm(
      `Excluir "${target.name}" (${target.email})?\n\nEsta ação é irreversível e apaga TODOS os dados financeiros deste usuário (contas, transações, cartões, financiamentos etc.).`,
    )
    if (confirmed) {
      removeMutation.mutate(target.id)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Usuários</h1>
          <p className="text-sm text-muted-foreground">Área administrativa — visível apenas para administradores</p>
        </div>
        <Button
          onClick={() => {
            setEditing(null)
            setDialogOpen(true)
          }}
        >
          <Plus className="h-4 w-4" /> Novo usuário
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-card">
        {isLoading ? (
          <div className="p-4">
            <Skeleton className="h-48 w-full" />
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-10 text-center text-sm text-muted-foreground">Nenhum usuário cadastrado.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>E-mail</TableHead>
                <TableHead>Papel</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Criado em</TableHead>
                <TableHead className="w-20" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">
                    {u.name}
                    {u.id === currentUser?.id && (
                      <span className="ml-2 text-xs text-muted-foreground">(você)</span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{u.email}</TableCell>
                  <TableCell>
                    <Badge variant={u.role === "ADMIN" ? "default" : "outline"}>
                      {u.role === "ADMIN" ? "Administrador" : "Usuário"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={u.is_active ? "success" : "secondary"}>{u.is_active ? "Ativo" : "Inativo"}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(u.created_at)}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setEditing(u)
                          setDialogOpen(true)
                        }}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      {u.id !== currentUser?.id && (
                        <button
                          onClick={() => handleDelete(u)}
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

      <AdminUserFormDialog open={dialogOpen} onOpenChange={setDialogOpen} user={editing} />
    </div>
  )
}
