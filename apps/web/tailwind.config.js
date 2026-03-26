/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Deep navy base — luxurious M&A feel
        canvas: {
          DEFAULT: "#0a0d14",
          subtle: "#0f1420",
          card: "#131929",
          border: "#1e2840",
        },
        // Cool slate for secondary surfaces
        surface: {
          DEFAULT: "#1a2236",
          hover: "#1f2a42",
          active: "#243150",
        },
        // Gold accent — trust, premium
        gold: {
          DEFAULT: "#c9a84c",
          light: "#e0bb6e",
          dark: "#a07830",
          muted: "rgba(201,168,76,0.15)",
        },
        // Semantic risk colors
        risk: {
          high: "#e05252",
          medium: "#e09c3a",
          low: "#4cae8a",
        },
        text: {
          primary: "#e8ecf4",
          secondary: "#8a97b4",
          muted: "#4a5570",
        },
      },
      fontFamily: {
        display: ["DM Serif Display", "Georgia", "serif"],
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.5), 0 1px 4px rgba(0,0,0,0.4)",
        gold: "0 0 0 1px rgba(201,168,76,0.4)",
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-in": "slideIn 0.25s ease-out",
      },
      keyframes: {
        fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } },
        slideIn: {
          from: { opacity: 0, transform: "translateY(6px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
