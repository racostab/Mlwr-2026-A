import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo, el navegador pega contra este Vite (puerto 5173) y se hace
// proxy hacia el motor (FastAPI :8001) y el servicio dinámico del host (:8002).
// En producción, nginx hace el mismo proxy (ver nginx.conf), así que el front
// siempre llama a rutas relativas: /api/... y /dynamic/...
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.ENGINE_URL || "http://localhost:8001",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
      "/dynapi": {
        target: process.env.DYNAMIC_URL || "http://localhost:8002",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/dynapi/, ""),
      },
    },
  },
});
