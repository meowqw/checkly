import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "@/components/Layout";
import ProtectedRoute from "@/components/ProtectedRoute";
import { AuthProvider } from "@/context/AuthContext";
import { SyncProvider } from "@/context/SyncContext";
import AccountsPage from "@/pages/AccountsPage";
import AddTransactionPage from "@/pages/AddTransactionPage";
import CategoriesPage from "@/pages/CategoriesPage";
import DashboardPage from "@/pages/DashboardPage";
import LoginPage from "@/pages/LoginPage";
import QrPage from "@/pages/QrPage";
import SettingsPage from "@/pages/SettingsPage";
import TransactionsPage from "@/pages/TransactionsPage";

export default function App() {
  return (
    <AuthProvider>
      <SyncProvider>
        <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="transactions" element={<TransactionsPage />} />
            <Route path="add" element={<AddTransactionPage />} />
            <Route path="qr" element={<QrPage />} />
            <Route path="accounts" element={<AccountsPage />} />
            <Route path="categories" element={<CategoriesPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </SyncProvider>
    </AuthProvider>
  );
}
