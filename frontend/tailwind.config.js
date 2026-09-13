/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        port: {
          bg: '#0b1220',
          panel: '#111a2c',
          line: '#1e2a44',
          accent: '#38bdf8',
        },
      },
    },
  },
  plugins: [],
}
