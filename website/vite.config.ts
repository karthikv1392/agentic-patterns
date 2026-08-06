import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/agentic-patterns/",
  plugins: [react()],
  build: {
    outDir: "dist",
  },
});
