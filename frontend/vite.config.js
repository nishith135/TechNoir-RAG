import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/auth": "http://localhost:8000",
      "/upload": "http://localhost:8000",
      "/query": "http://localhost:8000",
      "/collections": "http://localhost:8000",
      "/evaluate": "http://localhost:8000",
    },
  },
});
