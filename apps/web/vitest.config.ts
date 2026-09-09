import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(currentDirectory, "./src") } },
  test: {
    environment: "jsdom",
    environmentOptions: { jsdom: { url: "http://127.0.0.1:3100" } },
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      include: [
        "src/features/**/*.{ts,tsx}",
        "src/lib/api/**/*.{ts,tsx}",
        "src/app/api/v1/[...path]/route.ts",
      ],
      thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 },
      exclude: ["src/test/**"],
    },
  },
});
