import { defineConfig } from "@umijs/max";
import routes from "./routes";

const backendURL = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";

export default defineConfig({
  title: "Pinjie Console",
  favicons: ["/favicon.ico"],
  plugins: ["./config/html-accessibility"],
  ...(process.env.E2E_DISABLE_MFSU === "1" ? { mfsu: false } : {}),
  antd: {},
  access: {},
  model: {},
  initialState: {},
  layout: {},
  routes,
  history: { type: "browser" },
  hash: false,
  esbuildMinifyIIFE: true,
  npmClient: "pnpm",
  proxy: {
    "/api/v1": {
      target: backendURL,
      changeOrigin: false,
    },
    "/static/uploads": {
      target: backendURL,
      changeOrigin: false,
    },
    "/static/settings": {
      target: backendURL,
      changeOrigin: false,
    },
  },
  define: {
    "process.env.APP_ENV": process.env.APP_ENV ?? "development",
    "process.env.VITE_API_URL": process.env.VITE_API_URL ?? "",
  },
});
