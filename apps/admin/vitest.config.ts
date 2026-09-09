import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  resolve: {
    alias: { "@": path.resolve(import.meta.dirname, "src") },
  },
  test: {
    environment: "jsdom",
    environmentOptions: { jsdom: { url: "http://127.0.0.1:3101" } },
    testTimeout: 120_000,
    hookTimeout: 60_000,
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      include: ["src/features/**/*.{ts,tsx}", "src/lib/api/**/*.{ts,tsx}", "src/access.ts", "src/app.tsx"],
      thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 },
      exclude: ["src/test/**"],
    },
  },
});
