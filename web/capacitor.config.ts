import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.financemanager.app",
  appName: "Finance Manager",
  webDir: "dist",
  server: {
    androidScheme: "https",
  },
};

export default config;
