/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-dark': '#0b0f19',
        'brand-teal': '#45b8ac',
        'brand-teal-dark': '#35968b',
        'brand-teal-light': '#66c9bf',
        'brand-gray': '#1e2532',
      }
    },
  },
  plugins: [],
}
