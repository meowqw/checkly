/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          DEFAULT: "#16a34a",
          dark: "#15803d",
          light: "#dcfce7",
          muted: "#f0fdf4",
        },
      },
      spacing: {
        "safe-b": "env(safe-area-inset-bottom, 0px)",
        "safe-t": "env(safe-area-inset-top, 0px)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "fade-out": {
          from: { opacity: "1" },
          to: { opacity: "0" },
        },
        "page-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(100%)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fab-rise": {
          from: { opacity: "0", transform: "translateY(16px) scale(0.92)" },
          to: { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.95)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "pulse-soft": {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.04)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out forwards",
        "fade-out": "fade-out 0.15s ease-in forwards",
        "page-in": "page-in 0.35s cubic-bezier(0.22, 1, 0.36, 1) forwards",
        "slide-up": "slide-up 0.35s cubic-bezier(0.22, 1, 0.36, 1) forwards",
        "fab-rise": "fab-rise 0.35s cubic-bezier(0.22, 1, 0.36, 1) forwards",
        "scale-in": "scale-in 0.25s ease-out forwards",
        "pulse-soft": "pulse-soft 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
