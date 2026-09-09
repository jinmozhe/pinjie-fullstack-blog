import { pinjieConfig } from "@pinjie/eslint-config";
import nextPlugin from "@next/eslint-plugin-next";

export default [
  { ignores: [".next/**", "coverage/**"] },
  ...pinjieConfig,
  {
    languageOptions: {
      globals: {
        document: "readonly",
        Event: "readonly",
        FormData: "readonly",
        Headers: "readonly",
        HTMLFormElement: "readonly",
        Request: "readonly",
        RequestInit: "readonly",
        Response: "readonly",
        URL: "readonly",
        fetch: "readonly",
        process: "readonly",
        window: "readonly",
      },
    },
  },
  {
    plugins: {
      "@next/next": nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs["core-web-vitals"].rules,
    },
  },
];
