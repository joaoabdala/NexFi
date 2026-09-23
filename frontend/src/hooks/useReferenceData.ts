import { useQuery } from "@tanstack/react-query"
import { accountsApi } from "@/api/accounts"
import { categoriesApi } from "@/api/categories"
import { institutionsApi } from "@/api/institutions"
import type { Category } from "@/types"

export function useAccounts() {
  return useQuery({ queryKey: ["accounts"], queryFn: accountsApi.list })
}

export function useInstitutions() {
  return useQuery({ queryKey: ["institutions"], queryFn: institutionsApi.list })
}

export function useCategories() {
  return useQuery({ queryKey: ["categories"], queryFn: categoriesApi.list })
}

export interface FlatCategoryOption {
  id: string
  label: string
  kind: Category["kind"]
}

/**
 * Lista plana de categorias para selects. Por padrão só as ATIVAS — a API recusa lançamento em
 * categoria desativada, então oferecê-la no formulário só gerava erro. Filtros de listagem
 * (ex.: página de transações) passam `includeInactive` para achar lançamentos antigos.
 */
export function flattenCategories(
  categories: Category[],
  { includeInactive = false }: { includeInactive?: boolean } = {},
): FlatCategoryOption[] {
  const result: FlatCategoryOption[] = []
  for (const parent of categories) {
    if (!includeInactive && !parent.active) continue
    result.push({ id: parent.id, label: parent.name, kind: parent.kind })
    for (const child of parent.children ?? []) {
      if (!includeInactive && !child.active) continue
      result.push({ id: child.id, label: `${parent.name} › ${child.name}`, kind: child.kind })
    }
  }
  return result
}
