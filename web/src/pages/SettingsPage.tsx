import { useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <>
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Настройки</h1>
        <p className="mt-1 text-neutral-500">Профиль и выход</p>
      </header>

      <Card className="max-w-md rounded-3xl">
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-neutral-500">Логин</p>
            <p className="font-medium">{user?.login}</p>
          </div>
          <div>
            <p className="text-sm text-neutral-500">Email</p>
            <p className="font-medium">{user?.email}</p>
          </div>
          <Button variant="outline" className="w-full gap-2" onClick={handleLogout}>
            <LogOut size={16} /> Выйти
          </Button>
        </CardContent>
      </Card>
    </>
  );
}
