/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          800: "#064e3b",
          900: "#022c22",
          950: "#011c15",
        },
        agri: {
          light: "#f0fdf4",
          surface: "#ffffff",
          primary: "#059669",
          hover: "#047857",
          dark: "#065f46"
        }
      }
    },
  },
  plugins: [],
};
