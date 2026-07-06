/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'danger': '#dc2626',
        'warning': '#ea580c',
        'caution': '#ca8a04',
      },
    },
  },
  plugins: [],
}
