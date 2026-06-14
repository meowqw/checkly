import { Navigate, Outlet } from "react-router-dom";
import { AccountsProvider } from "@/context/AccountsContext";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return (
    <AccountsProvider>
      <Outlet />
    </AccountsProvider>
  );
}
