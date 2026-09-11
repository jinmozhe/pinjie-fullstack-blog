import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        sidebar: "var(--sidebar)",
        card: { DEFAULT: "var(--card)", foreground: "var(--card-foreground)" },
        popover: { DEFAULT: "var(--popover)", foreground: "var(--popover-foreground)" },
        success: { DEFAULT: "var(--success)", foreground: "var(--success-foreground)" },
        warning: { DEFAULT: "var(--warning)", foreground: "var(--warning-foreground)" },
        disabled: { DEFAULT: "var(--muted)", foreground: "var(--disabled-foreground)" },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        link: { DEFAULT: "var(--link)", hover: "var(--link-hover)" },
        error: {
          DEFAULT: "var(--error)",
          foreground: "var(--error-foreground)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        serif: ["var(--font-serif)"],
        mono: ["var(--font-mono)"],
      },
      fontSize: {
        base: ["var(--text-base)", "1.5"],
        ui: ["var(--text-ui)", "1.5"],
        meta: ["var(--text-meta)", "1.5"],
        "card-title": ["var(--text-card-title)", "1.4"],
        "home-title": ["var(--text-home-title)", "1.35"],
        "article-title": ["var(--text-article-title)", "1.3"],
        section: ["var(--text-section-title)", "1.4"],
      },
      borderRadius: {
        control: "var(--radius-control)",
        media: "var(--radius-media)",
        card: "var(--radius-card)",
        pill: "var(--radius-pill)",
      },
      boxShadow: { card: "var(--shadow-card)" },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        5: "var(--space-5)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        10: "var(--space-10)",
        12: "var(--space-12)",
        16: "var(--space-16)",
        grid: "var(--gap-grid)",
        section: "var(--gap-section)",
        card: "var(--padding-card)",
        page: "var(--page-gutter)",
      },
      transitionDuration: {
        hover: "var(--duration-hover)",
        panel: "var(--duration-panel)",
      },
    },
  },
  plugins: [animate],
};

export default config;
