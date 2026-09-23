import { cn } from "@/lib/utils"

const INSTITUTIONAL_SITE = "https://www.abdalanexus.com/"

/**
 * Footer padrão dos apps Abdala Nexus (mesmo desenho do NexGarage): uma "estrada" escura com linha
 * teal no topo, o ícone do produto quicando sobre a linha — aqui o "N em alta" — e o crédito com
 * link para o site institucional.
 */
export function AppFooter({ className }: { className?: string }) {
  return (
    <footer className={cn("relative h-14 w-full shrink-0 select-none sm:h-16", className)} style={{ background: "var(--road)" }}>
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-[3px]" style={{ background: "rgba(20, 187, 166, 0.5)" }} />

      <div aria-hidden="true" className="animate-nexfi-bounce absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2">
        {/* Linhas de velocidade atrás do ícone */}
        <div className="absolute right-full top-1/2 mr-1 flex -translate-y-1/2 flex-col gap-1 opacity-60">
          <div className="h-0.5 w-4 rounded-full" style={{ background: "rgba(20, 187, 166, 0.6)" }} />
          <div className="h-0.5 w-3 rounded-full" style={{ background: "rgba(20, 187, 166, 0.4)" }} />
          <div className="h-0.5 w-5 rounded-full" style={{ background: "rgba(20, 187, 166, 0.5)" }} />
        </div>
        <svg width="34" height="34" viewBox="0 0 64 64" className="drop-shadow-md">
          <path d="M19 46V19L45 45V21" fill="none" stroke="#14BBA6" strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="45" cy="18" r="5.5" fill="#5EEEA4" />
        </svg>
      </div>

      {/* Cores fixas: a faixa é escura nos dois temas (o --primary do tema claro some no fundo escuro). */}
      <p className="absolute inset-x-0 bottom-3 text-center text-xs sm:bottom-4" style={{ color: "#94A3B8" }}>
        <a
          href={INSTITUTIONAL_SITE}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-sm px-1 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#14BBA6]"
        >
          © {new Date().getFullYear()} <span className="font-medium" style={{ color: "#14BBA6" }}>Abdala Nexus</span>
        </a>
      </p>
    </footer>
  )
}
