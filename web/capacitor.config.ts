import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.financemanager.app",
  appName: "Checkly alfa",
  webDir: "dist",
  server: {
    // http — иначе WebView (https://localhost) блокирует запросы на http://IP:8000
    androidScheme: "http",
  },
};

export default config;
