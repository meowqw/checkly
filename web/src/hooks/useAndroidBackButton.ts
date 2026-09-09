import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { App as CapApp } from "@capacitor/app";
import { Capacitor } from "@capacitor/core";

type Options = {
  /** Вернуть true, если событие уже обработано (например закрыт FAB). */
  intercept?: () => boolean;
};

/** Hardware back: с /add, /qr и вложенных экранов — назад; с корня — выход. */
export function useAndroidBackButton(options?: Options) {
  const navigate = useNavigate();
  const location = useLocation();
  const intercept = options?.intercept;

  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return;

    const sub = CapApp.addListener("backButton", () => {
      if (intercept?.()) return;
      const path = location.pathname;
      if (path === "/" || path === "") {
        void CapApp.exitApp();
        return;
      }
      if (window.history.length > 1) {
        navigate(-1);
        return;
      }
      navigate("/", { replace: true });
    });

    return () => {
      void sub.then((handle) => handle.remove());
    };
  }, [navigate, location.pathname, intercept]);
}
