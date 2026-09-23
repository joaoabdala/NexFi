import { useState } from "react"
import { NavLink } from "react-router-dom"
import { useAuth } from "@/contexts/AuthContext"
import { cn } from "@/lib/utils"
import { navSections } from "./nav-config"
import { BrandMark } from "@/components/BrandMark"
import { AppFooter } from "@/components/AppFooter"

function visibleFor(items: typeof navSections, isAdmin: boolean): typeof navSections {
  return items
    .filter((item) => !item.adminOnly || isAdmin)
    .map((item) => (item.children ? { ...item, children: visibleFor(item.children, isAdmin) } : item))
}

function Logo() {
  return (
    <div className="flex items-center gap-2 px-2">
      <BrandMark className="h-8 w-8 shrink-0" />
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
      <nav className="-mx-1 flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-1 scrollbar-thin">
        {items.map((item) => (
          <NavGroup key={item.label} item={item} onNavigate={onNavigate} />
        ))}
      </nav>
      <AppFooter className="border-t border-border pt-4" />
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
