/** @type {import('tailwindcss').Config} */

// Helper: reference a CSS variable as rgb channels so Tailwind opacity modifiers work
const c = (name) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: c("canvas"),
          subtle: c("canvas-subtle"),
          card: c("canvas-card"),
          border: c("canvas-border"),
        },
        surface: {
          DEFAULT: c("surface"),
          hover: c("surface-hover"),
          active: c("surface-active"),
        },
        gold: {
          DEFAULT: c("gold"),
          light: c("gold-light"),
          dark: c("gold-dark"),
          muted: "var(--gold-muted)",
        },
        highlight: {
          DEFAULT: c("highlight"),
          light: c("highlight-light"),
          dark: c("highlight-dark"),
          muted: "var(--highlight-muted)",
        },
        risk: {
          high: c("risk-high"),
          medium: c("risk-medium"),
          low: c("risk-low"),
        },
        text: {
          primary: c("text-primary"),
          secondary: c("text-secondary"),
          muted: c("text-muted"),
        },
      },
      fontFamily: {
        display: ["DM Serif Display", "Georgia", "serif"],
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        xs: ["0.8125rem", { lineHeight: "1.25rem" }],
        sm: ["0.9375rem", { lineHeight: "1.375rem" }],
        base: ["1.0625rem", { lineHeight: "1.625rem" }],
        lg: ["1.1875rem", { lineHeight: "1.75rem" }],
        xl: ["1.3125rem", { lineHeight: "1.875rem" }],
        "2xl": ["1.625rem", { lineHeight: "2rem" }],
        "3xl": ["2rem", { lineHeight: "2.375rem" }],
      },
      borderRadius: {
        sm: "6px",
        DEFAULT: "8px",
        md: "10px",
        lg: "14px",
        xl: "18px",
        "2xl": "24px",
      },
      boxShadow: {
        card: "var(--shadow-card)",
        "card-hover": "var(--shadow-card-hover)",
        elevated: "var(--shadow-elevated)",
        gold: "0 0 0 1px rgba(200,169,106,0.35)",
        "gold-glow": "0 0 20px rgba(200,169,106,0.15)",
      },
      spacing: {
        4.5: "1.125rem",
        13: "3.25rem",
        15: "3.75rem",
        18: "4.5rem",
      },
      animation: {
        "fade-in": "fadeIn 0.25s ease-out",
        "slide-in": "slideIn 0.3s ease-out",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } },
        slideIn: {
          from: { opacity: 0, transform: "translateY(8px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
        glow: {
          from: { boxShadow: "0 0 5px rgba(200,169,106,0.1)" },
          to: { boxShadow: "0 0 20px rgba(200,169,106,0.2)" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
