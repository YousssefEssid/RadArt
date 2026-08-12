/** @type {import('tailwindcss').Config} */
/** Charte RadArt: navy + lime, canvas papier (Pinterest), sidebar ink (Meltwater / Sprinklr). */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        display: ["Syne", "system-ui", "sans-serif"],
      },
      colors: {
        radj: {
          navy: "#1C1C68",
          lime: "#D7FF7B",
          white: "#FFFFFF",
          black: "#000000",
          ink: "#12142B",
          canvas: "#F3F1EC",
          mist: "#E8E6E0",
          sand: "#FAF9F6",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(18, 20, 43, 0.04), 0 8px 24px -12px rgba(18, 20, 43, 0.12)",
      },
    },
  },
  plugins: [],
};
