/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        forge: {
          /* space: pure black base, barely-there surfaces */
          bg:             "#000000",
          surface:        "#09090F",
          surface2:       "#0E0E1A",
          border:         "#161625",
          "border-hover": "#252540",
          /* star whites */
          "text-dim":     "rgba(255,255,255,0.35)",
          "text-mid":     "rgba(255,255,255,0.60)",
        },
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "star-drift": "star-drift 8s ease-in-out infinite alternate",
      },
      keyframes: {
        "star-drift": {
          "0%":   { opacity: "0.4", transform: "scale(1)" },
          "100%": { opacity: "0.8", transform: "scale(1.05)" },
        },
      },
    },
  },
  plugins: [],
};
