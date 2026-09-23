/**
 * Logo do NexFi ("N em alta"): a letra N desenhada como a linha de um gráfico que termina no
 * ponto mais alto. Mesma arte de public/favicon.svg — ao mudar uma, mude a outra (e regenere os
 * PNGs com scripts/generate-brand-assets.mjs).
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} role="img" aria-label="NexFi">
      <rect width="64" height="64" rx="14" fill="#0B0F19" />
      <path
        d="M19 46V19L45 45V21"
        fill="none"
        stroke="#14BBA6"
        strokeWidth={7}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="45" cy="18" r="5.5" fill="#5EEEA4" />
    </svg>
  )
}
