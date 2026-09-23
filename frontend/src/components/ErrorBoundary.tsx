import { Component, type ErrorInfo, type ReactNode } from "react"
import { Button } from "@/components/ui/button"

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/**
 * Sem um boundary, qualquer erro de renderização (ou um chunk lazy que falhou ao carregar)
 * desmonta a árvore inteira e o usuário fica com uma tela em branco.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Erro não tratado na interface", error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div role="alert" className="flex flex-col items-start gap-3 rounded-lg border border-border p-6">
        <h2 className="text-lg font-semibold">Algo deu errado ao exibir esta tela.</h2>
        <p className="text-sm text-muted-foreground">
          Se o NexFi acabou de ser atualizado, recarregar a página resolve.
        </p>
        <Button onClick={() => window.location.reload()}>Recarregar</Button>
      </div>
    )
  }
}
