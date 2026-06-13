/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Paleta institucional ESCOM / IPN: el guinda es la marca.
        guinda: {
          50: "#fbf1f5",
          100: "#f7e2ec",
          200: "#eebcd0",
          300: "#e088ab",
          400: "#d05683",
          500: "#b03363",
          600: "#8e1d4b",
          700: "#6d1238", // guinda institucional
          800: "#4f0d29",
          900: "#3a0a1f",
          950: "#220511",
        },
        // Acento dorado/ámbar (detalle institucional sobrio).
        oro: {
          300: "#f3d58a",
          400: "#e9bf5b",
          500: "#d6a32f",
        },
        // Superficies del tema oscuro "consola de laboratorio".
        ink: {
          950: "#0a0710",
          900: "#0f0b16",
          850: "#140f1d",
          800: "#1a1424",
          700: "#241a31",
          600: "#33263f",
        },
        line: "#2b2138",
        "line-strong": "#3c2e4d",
        ok: "#34d399",
        warn: "#fbbf24",
        danger: "#f87171",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        display: ["Sora", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(176,51,99,0.25), 0 18px 50px -20px rgba(176,51,99,0.55)",
        card: "0 20px 50px -30px rgba(0,0,0,0.8)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-700px 0" },
          "100%": { backgroundPosition: "700px 0" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(.8)", opacity: "0.6" },
          "100%": { transform: "scale(2.2)", opacity: "0" },
        },
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        "grid-pan": {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "60px 60px" },
        },
      },
      animation: {
        shimmer: "shimmer 1.6s linear infinite",
        "pulse-ring": "pulse-ring 1.8s cubic-bezier(0.4,0,0.2,1) infinite",
        float: "float 6s ease-in-out infinite",
        "grid-pan": "grid-pan 18s linear infinite",
      },
    },
  },
  plugins: [],
};
