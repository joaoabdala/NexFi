import { useState } from "react"
import { NavLink } from "react-router-dom"
import { useAuth } from "@/contexts/AuthContext"
import { cn } from "@/lib/utils"
import { navSections } from "./nav-config"

function visibleFor(items: typeof navSections, isAdmin: boolean): typeof navSections {
  return items
    .filter((item) => !item.adminOnly || isAdmin)
    .map((item) => (item.children ? { ...item, children: visibleFor(item.children, isAdmin) } : item))
}

function Logo() {
  return (
    <div className="flex items-center gap-2 px-2">
      <svg viewBox="0 0 64 64" className="h-8 w-8 shrink-0">
        <defs>
          <linearGradient id="logo-g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#14BBA6" />
            <stop offset="1" stopColor="#5EEEA4" />
          </linearGradient>
        </defs>
        <rect width="64" height="64" rx="14" fill="#0B0F19" />
        <path
          d="M16 46 L27 18 L32 18 L24 40 L40 40 L48 18 L48 46 L43 46 L43 26 L36 46 L30 46 L38 24 L32 40 L23 40 Z"
          fill="url(#logo-g)"
        />
      </svg>
      <div className="leading-tight">
        <p className="font-heading text-base font-semibold">NexFi</p>
        <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Abdala Nexus</p>
      </div>
    </div>
  )
}

function NavGroup({ item, onNavigate }: { item: (typeof navSections)[number]; onNavigate?: () => void }) {
  const [open, setOpen] = useState(true)
  const Icon = item.icon

  if (!item.children) {
    return (
      <NavLink
        to={item.to!}
        end={item.to === "/"}
        onClick={onNavigate}
        className={({ isActive }) =>
          cn(
            "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
            isActive ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-secondary hover:text-foreground",
          )
        }
      >
        <Icon className="h-4 w-4" />
        {item.label}
      </NavLink>
    )
  }

  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
      >
        <Icon className="h-4 w-4" />
        {item.label}
      </button>
      {open && (
        <div className="ml-4 mt-1 flex flex-col gap-0.5 border-l border-border pl-3">
          {item.children.map((child) => (
            <NavLink
              key={child.to}
              to={child.to!}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors",
                  isActive
                    ? "bg-primary/15 text-primary font-medium"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                )
              }
            >
              <child.icon className="h-3.5 w-3.5" />
              {child.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuth()
  const items = visibleFor(navSections, user?.role === "ADMIN")

  return (
    <div className="flex h-full flex-col gap-6 px-3 py-5">
      <Logo />
      <nav className="flex flex-col gap-1">
        {items.map((item) => (
          <NavGroup key={item.label} item={item} onNavigate={onNavigate} />
        ))}
      </nav>
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-border bg-card lg:block">
      <SidebarContent />
    </aside>
  )
}
