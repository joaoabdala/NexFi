import {
  ArrowLeftRight,
  Building2,
  CreditCard,
  LandPlot,
  LayoutDashboard,
  Repeat,
  ShieldCheck,
  Tags,
  Target,
  TrendingUp,
  UserCircle,
  Users,
  Wallet,
  Wallet2,
} from "lucide-react"

export interface NavItem {
  label: string
  to?: string
  icon: typeof LayoutDashboard
  children?: NavItem[]
  adminOnly?: boolean
}

export const navSections: NavItem[] = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard },
  { label: "Transações", to: "/transacoes", icon: ArrowLeftRight },
  {
    label: "Financeiro",
    icon: Wallet,
    children: [
      { label: "Contas", to: "/financeiro/contas", icon: Wallet2 },
      { label: "Cartões", to: "/financeiro/cartoes", icon: CreditCard },
      { label: "Financiamentos", to: "/financeiro/financiamentos", icon: LandPlot },
      { label: "Rendimentos", to: "/financeiro/rendimentos", icon: TrendingUp },
    ],
  },
  {
    label: "Planejamento",
    icon: Target,
    children: [
      { label: "Orçamentos", to: "/planejamento/orcamentos", icon: Wallet },
      { label: "Metas", to: "/planejamento/metas", icon: Target },
    ],
  },
  {
    label: "Configurações",
    icon: Tags,
    children: [
      { label: "Categorias", to: "/configuracoes/categorias", icon: Tags },
      { label: "Instituições", to: "/configuracoes/instituicoes", icon: Building2 },
      { label: "Recorrências", to: "/configuracoes/recorrencias", icon: Repeat },
      { label: "Perfil", to: "/configuracoes/perfil", icon: UserCircle },
    ],
  },
  {
    label: "Administração",
    icon: ShieldCheck,
    adminOnly: true,
    children: [{ label: "Usuários", to: "/admin/usuarios", icon: Users, adminOnly: true }],
  },
]
