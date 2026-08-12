/** @type {import('tailwindcss').Config} */
/** Charte radj: lime #D7FF7B, navy #1C1C68, blanc #FFFFFF, noir #000000 — typos cible TS Deniz + 29LT Adir */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Corps: proche 29LT Adir (géométrique lisible) — remplacer par fichiers 29LT si licence
        sans: ["DM Sans", "system-ui", "sans-serif"],
        // Titres / logo: proche TS Deniz — remplacer par fichiers TypeType si licence
        display: ["Syne", "system-ui", "sans-serif"],
      },
      colors: {
        radj: {
          navy: "#1C1C68",
          lime: "#D7FF7B",
          white: "#FFFFFF",
          black: "#000000",
        },
      },
    },
  },
  plugins: [],
};
