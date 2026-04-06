/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Deep dark base — luxurious M&A feel
        canvas: {
          DEFAULT: "#0B0F14",
          subtle: "#101620",
          card: "#121821",
          border: "#1E2A3A",
        },
        // Elevated surfaces
        surface: {
          DEFAULT: "#1A2230",
          hover: "#1F2A3A",
          active: "#253344",
        },
        // Gold accent — trust, premium, primary CTA
        gold: {
          DEFAULT: "#C8A96A",
          light: "#DBBF82",
          dark: "#A08040",
          muted: "rgba(200,169,106,0.12)",
        },
        // Blue highlight — secondary accent
        highlight: {
          DEFAULT: "#4A90E2",
          light: "#6AA8F0",
          dark: "#3570B8",
          muted: "rgba(74,144,226,0.12)",
        },
        // Semantic risk colors
        risk: {
          high: "#E05252",
          medium: "#E09C3A",
          low: "#4CAE8A",
        },
        // Text hierarchy
        text: {
          primary: "#E6EAF0",
          secondary: "#A0A8B8",
          muted: "#566278",
        },
      },
      fontFamily: {
        display: ["DM Serif Display", "Georgia", "serif"],
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        // Slightly larger defaults for readability
        xs: ["0.8125rem", { lineHeight: "1.25rem" }],    // 13px
        sm: ["0.9375rem", { lineHeight: "1.375rem" }],   // 15px
        base: ["1.0625rem", { lineHeight: "1.625rem" }], // 17px
        lg: ["1.1875rem", { lineHeight: "1.75rem" }],    // 19px
        xl: ["1.3125rem", { lineHeight: "1.875rem" }],   // 21px
        "2xl": ["1.625rem", { lineHeight: "2rem" }],     // 26px
        "3xl": ["2rem", { lineHeight: "2.375rem" }],     // 32px
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
        card: "0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)",
        "card-hover": "0 8px 24px rgba(0,0,0,0.4), 0 2px 8px rgba(0,0,0,0.3)",
        elevated: "0 4px 16px rgba(0,0,0,0.35)",
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
        "glow": "glow 2s ease-in-out infinite alternate",
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
