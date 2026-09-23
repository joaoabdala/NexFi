const GRID_COLS = 14
const GRID_ROWS = 18
const GLOW_COLORS = ["rgba(20,187,166,", "rgba(94,238,164,"]

interface GlowCell {
  index: number
  delay: number
  duration: number
  color: string
}

function buildGlowCells(): GlowCell[] {
  const cells: GlowCell[] = []
  const total = GRID_COLS * GRID_ROWS
  for (let i = 0; i < total; i++) {
    if (Math.random() < 0.1) {
      cells.push({
        index: i,
        delay: Math.random() * 6,
        duration: 3 + Math.random() * 3,
        color: GLOW_COLORS[Math.floor(Math.random() * GLOW_COLORS.length)],
      })
    }
  }
  return cells
}

function QuadrantGrid() {
  const glowCells = buildGlowCells()
  const glowByIndex = new Map(glowCells.map((c) => [c.index, c]))

  return (
    <div
      className="absolute inset-0 grid"
      style={{ gridTemplateColumns: `repeat(${GRID_COLS}, 1fr)`, gridTemplateRows: `repeat(${GRID_ROWS}, 1fr)` }}
      aria-hidden
    >
      {Array.from({ length: GRID_COLS * GRID_ROWS }).map((_, i) => {
        const glow = glowByIndex.get(i)
        return (
          <div key={i} className="border border-white/[0.05]">
            {glow && (
              <div
                className="animate-nexfi-quadrant-glow h-full w-full"
                style={{
                  backgroundColor: `${glow.color}0.18)`,
                  boxShadow: `inset 0 0 18px 2px ${glow.color}0.45)`,
                  animationDelay: `${glow.delay}s`,
                  animationDuration: `${glow.duration}s`,
                }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

const NODES = [
  { x: 60, y: 90 }, { x: 180, y: 60 }, { x: 300, y: 110 }, { x: 420, y: 70 },
  { x: 120, y: 200 }, { x: 260, y: 220 }, { x: 400, y: 190 }, { x: 40, y: 320 },
  { x: 200, y: 340 }, { x: 340, y: 320 }, { x: 460, y: 300 }, { x: 100, y: 440 },
  { x: 260, y: 460 }, { x: 400, y: 430 }, { x: 180, y: 540 }, { x: 340, y: 560 },
]

const LINKS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [1, 4], [2, 5], [3, 6], [4, 5], [5, 6], [4, 7],
  [5, 8], [6, 9], [6, 10], [7, 8], [8, 9], [9, 10], [8, 11], [9, 12],
  [10, 13], [11, 12], [12, 13], [11, 14], [12, 15], [13, 15], [14, 15],
]

export function LoginVisual() {
  return (
    <div className="relative hidden h-full w-full overflow-hidden bg-nexfi-midnight lg:block">
      {/* Glow orbs */}
      <div
        className="animate-nexfi-float absolute -left-24 -top-24 h-[28rem] w-[28rem] rounded-full bg-nexfi-teal/40 blur-3xl"
        aria-hidden
      />
      <div
        className="animate-nexfi-float-slow absolute bottom-[-8rem] right-[-6rem] h-[32rem] w-[32rem] rounded-full bg-nexfi-teal-light/25 blur-3xl"
        aria-hidden
      />
      <div
        className="animate-nexfi-float-accent absolute left-1/3 top-1/2 h-72 w-72 rounded-full bg-nexfi-teal/20 blur-3xl"
        aria-hidden
      />

      {/* Scan sweep */}
      <div
        className="animate-nexfi-scan pointer-events-none absolute -left-1/2 -top-1/2 h-[200%] w-32 bg-gradient-to-b from-transparent via-nexfi-teal-light/25 to-transparent blur-xl"
        aria-hidden
      />

      {/* Grid com quadrantes acendendo e apagando */}
      <QuadrantGrid />

      {/* Network */}
      <svg
        viewBox="0 0 500 620"
        className="absolute inset-0 h-full w-full"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden
      >
        <defs>
          <linearGradient id="nexfi-line" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#14BBA6" />
            <stop offset="1" stopColor="#5EEEA4" />
          </linearGradient>
        </defs>
        <g className="animate-nexfi-rotate-slow">
          {LINKS.map(([a, b], i) => (
            <line
              key={`${a}-${b}`}
              x1={NODES[a].x}
              y1={NODES[a].y}
              x2={NODES[b].x}
              y2={NODES[b].y}
              stroke="url(#nexfi-line)"
              strokeWidth={1}
              strokeOpacity={0.4}
              strokeDasharray="4 6"
              className="animate-nexfi-drift"
              style={{ animationDelay: `${(i % 6) * 0.4}s`, animationDuration: `${6 + (i % 5)}s` }}
            />
          ))}
          {NODES.map((n, i) => (
            <circle
              key={i}
              cx={n.x}
              cy={n.y}
              r={i % 3 === 0 ? 3.5 : 2.5}
              fill={i % 2 === 0 ? "#14BBA6" : "#5EEEA4"}
              className="animate-nexfi-pulse-soft"
              style={{ animationDelay: `${(i % 7) * 0.3}s` }}
            />
          ))}
        </g>
      </svg>

      {/* Content */}
      <div className="relative flex h-full flex-col justify-between p-12 xl:p-16">
        <div className="flex items-center gap-2.5">
          <svg viewBox="0 0 64 64" className="h-9 w-9 shrink-0">
            <defs>
              <linearGradient id="visual-logo-g" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#14BBA6" />
                <stop offset="1" stopColor="#5EEEA4" />
              </linearGradient>
            </defs>
            <rect width="64" height="64" rx="14" fill="#0B0F19" />
            <path
              d="M16 46 L27 18 L32 18 L24 40 L40 40 L48 18 L48 46 L43 46 L43 26 L36 46 L30 46 L38 24 L32 40 L23 40 Z"
              fill="url(#visual-logo-g)"
            />
          </svg>
          <span className="font-heading text-lg font-semibold text-white">NexFi</span>
        </div>

        <div className="animate-nexfi-fade-in max-w-md" style={{ animationDelay: "0.15s" }}>
          <h2 className="font-heading text-4xl font-semibold leading-tight text-white xl:text-[2.75rem]">
            Tecnologia que <span className="text-nexfi-teal-light">conecta</span>.
            <br />
            Finanças que <span className="text-nexfi-teal-light">transformam</span>.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-white/60">
            Contas, cartões, financiamentos e metas em um único painel — com dados sempre
            precisos e sob controle.
          </p>
        </div>

        <p className="text-xs text-white/35">© {new Date().getFullYear()} Abdala Nexus</p>
      </div>
    </div>
  )
}
