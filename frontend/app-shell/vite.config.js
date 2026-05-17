import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/app-static/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
