import { Navigate, Route, Routes } from "react-router-dom"
import { AdminRoute } from "@/components/AdminRoute"
import { AppLayout } from "@/components/layout/AppLayout"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { AccountsPage } from "@/pages/AccountsPage"
import { AdminUsersPage } from "@/pages/AdminUsersPage"
import { BudgetsPage } from "@/pages/BudgetsPage"
import { CardsPage } from "@/pages/CardsPage"
import { CategoriesPage } from "@/pages/CategoriesPage"
import { DashboardPage } from "@/pages/DashboardPage"
import { FinancingPage } from "@/pages/FinancingPage"
import { GoalsPage } from "@/pages/GoalsPage"
import { InstitutionsPage } from "@/pages/InstitutionsPage"
import { LoginPage } from "@/pages/LoginPage"
import { ProfilePage } from "@/pages/ProfilePage"
import { RecurrencesPage } from "@/pages/RecurrencesPage"
import { TransactionsPage } from "@/pages/TransactionsPage"
import { YieldsPage } from "@/pages/YieldsPage"

export default function App() {
  return (
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
  )
}
