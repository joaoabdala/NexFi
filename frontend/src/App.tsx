import { lazy, Suspense } from "react"
import { Navigate, Route, Routes } from "react-router-dom"
import { AdminRoute } from "@/components/AdminRoute"
import { AppLayout } from "@/components/layout/AppLayout"
import { PageFallback } from "@/components/PageFallback"
import { ProtectedRoute } from "@/components/ProtectedRoute"

// Cada página vira um chunk próprio, baixado só quando a rota é acessada.
const AccountsPage = lazy(() => import("@/pages/AccountsPage").then((m) => ({ default: m.AccountsPage })))
const AdminUsersPage = lazy(() => import("@/pages/AdminUsersPage").then((m) => ({ default: m.AdminUsersPage })))
const BudgetsPage = lazy(() => import("@/pages/BudgetsPage").then((m) => ({ default: m.BudgetsPage })))
const CardsPage = lazy(() => import("@/pages/CardsPage").then((m) => ({ default: m.CardsPage })))
const CategoriesPage = lazy(() => import("@/pages/CategoriesPage").then((m) => ({ default: m.CategoriesPage })))
const DashboardPage = lazy(() => import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage })))
const FinancingPage = lazy(() => import("@/pages/FinancingPage").then((m) => ({ default: m.FinancingPage })))
const GoalsPage = lazy(() => import("@/pages/GoalsPage").then((m) => ({ default: m.GoalsPage })))
const InstitutionsPage = lazy(() => import("@/pages/InstitutionsPage").then((m) => ({ default: m.InstitutionsPage })))
const LoginPage = lazy(() => import("@/pages/LoginPage").then((m) => ({ default: m.LoginPage })))
const ProfilePage = lazy(() => import("@/pages/ProfilePage").then((m) => ({ default: m.ProfilePage })))
const RecurrencesPage = lazy(() => import("@/pages/RecurrencesPage").then((m) => ({ default: m.RecurrencesPage })))
const TransactionsPage = lazy(() => import("@/pages/TransactionsPage").then((m) => ({ default: m.TransactionsPage })))
const YieldsPage = lazy(() => import("@/pages/YieldsPage").then((m) => ({ default: m.YieldsPage })))

export default function App() {
  return (
    <Suspense fallback={<PageFallback fullScreen />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/transacoes" element={<TransactionsPage />} />
          <Route path="/financeiro/contas" element={<AccountsPage />} />
          <Route path="/financeiro/cartoes" element={<CardsPage />} />
          <Route path="/financeiro/financiamentos" element={<FinancingPage />} />
          <Route path="/financeiro/rendimentos" element={<YieldsPage />} />
          <Route path="/planejamento/orcamentos" element={<BudgetsPage />} />
          <Route path="/planejamento/metas" element={<GoalsPage />} />
          <Route path="/configuracoes/categorias" element={<CategoriesPage />} />
          <Route path="/configuracoes/instituicoes" element={<InstitutionsPage />} />
          <Route path="/configuracoes/recorrencias" element={<RecurrencesPage />} />
          <Route path="/configuracoes/perfil" element={<ProfilePage />} />
          <Route
            path="/admin/usuarios"
            element={
              <AdminRoute>
                <AdminUsersPage />
              </AdminRoute>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
