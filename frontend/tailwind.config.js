/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          600: '#4F46E5', // indigo-600
          700: '#4338CA', // indigo-700
        },
        purple: {
          600: '#7C3AED',
        },
        gray: {
          200: '#E5E7EB',
        }
      }
    },
  },
  plugins: [],
}
