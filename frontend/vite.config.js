import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "https://trustlessproof-backend-production.up.railway.app",
        changeOrigin: true,
        secure: true
      }
    }
  }
});
