/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        brand: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        port: {
          bg:          'var(--port-bg)',
          panel:       'var(--port-panel)',
          panelHover:  'var(--port-panel-hover)',
          line:        'var(--port-line)',
          text:        'var(--port-text)',
          muted:       'var(--port-muted)',
          accent:      'var(--port-accent)',
          accentLight: 'var(--port-accent-light)',
        },
      },
      boxShadow: {
        'card':      '0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)',
        'card-hover':'0 4px 12px 0 rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.04)',
        'soft':      '0 2px 8px -2px rgb(0 0 0 / 0.06)',
        'glow':      '0 0 20px -4px rgb(37 99 235 / 0.15)',
      },
    },
  },
  plugins: [],
};
