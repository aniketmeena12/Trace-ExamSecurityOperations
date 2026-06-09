import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend runs on :8000; proxy /api in dev so the browser hits one origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
