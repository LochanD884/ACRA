/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        midnight: "#06070a",
        neon: "#7dd3fc",
        cyan: "#38bdf8",
        magenta: "#ff2ea6",
        ember: "#f59e0b"
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        display: ["Bebas Neue", "Impact", "sans-serif"]
      },
      boxShadow: {
        glow: "0 0 25px rgba(57, 255, 20, 0.35)",
        cyan: "0 0 20px rgba(0, 229, 255, 0.4)"
      }
    }
  },
  plugins: []
};
