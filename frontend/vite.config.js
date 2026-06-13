import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend runs on :8000; proxy /api in dev so the browser hits one origin.
const apiProxy = {
  "/api": {
    target: "http://127.0.0.1:8000",
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ""),
  },
};

export default defineConfig({
  plugins: [react()],
  // Disable the filesystem watcher to avoid ENOSPC on constrained hosts; the
  // dev proxy keeps the browser on one origin. `preview` mirrors the proxy so
  // the built bundle can talk to the backend too.
  server: { port: 5173, proxy: apiProxy, watch: { ignored: ["**/*"] } },
  preview: { port: 4173, proxy: apiProxy },
});
