import { pinjieConfig } from "@pinjie/eslint-config";

export default [
  { ignores: ["coverage/**", "dist/**", "**/.umi/**", "**/.umi-production/**"] },
  ...pinjieConfig,
  {
    languageOptions: {
      globals: {
        document: "readonly",
        fetch: "readonly",
        Headers: "readonly",
        process: "readonly",
        RequestInit: "readonly",
        Response: "readonly",
        URLSearchParams: "readonly",
        window: "readonly",
      },
    },
  },
];
