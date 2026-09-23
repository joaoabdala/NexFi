import { Button } from "@/components/ui/button"

/** Estado de erro de carregamento — antes a tela ficava num skeleton eterno quando a API falhava. */
export function LoadError({ onRetry, message = "Não foi possível carregar os dados." }: { onRetry: () => void; message?: string }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-3 rounded-lg border border-border p-6">
      <p className="text-sm">{message}</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Tentar novamente
      </Button>
    </div>
  )
}
