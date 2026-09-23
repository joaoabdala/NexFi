import { cn } from "@/lib/utils"

const INSTITUTIONAL_SITE = "https://www.abdalanexus.com/"

/** Crédito padrão dos apps Abdala Nexus, com link para o site institucional. */
export function AppFooter({ className }: { className?: string }) {
  return (
    <footer className={cn("text-center text-xs text-muted-foreground", className)}>
      <a
        href={INSTITUTIONAL_SITE}
        target="_blank"
        rel="noopener noreferrer"
        className="rounded-sm px-1 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        © {new Date().getFullYear()} <span className="font-medium text-primary">Abdala Nexus</span>
      </a>
    </footer>
  )
}
