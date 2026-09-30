/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        graphite: '#0a0b0d',
        panel: '#12141a',
        'panel-raised': '#161922',
        teal: {
          400: '#2DD4BF',
          500: '#14b8a6',
          600: '#0d9488',
        },
        navy: '#1e3a5f',
        signal: {
          DEFAULT: '#f0a860',
          dim: '#f0a86040',
        },
        // Light theme surface tokens
        paper: '#fafaf8',
        'paper-raised': '#ffffff',
        ink: '#18181b',
      },
      fontFamily: {
        // All three tokens point to Inter now (user asked for Inter
        // "everywhere") — kept as three separate keys rather than
        // collapsing to one class name so nothing elsewhere in the
        // codebase needs to change (font-display/font-body/font-mono
        // still control size/weight/tracking via Tailwind utilities
        // applied alongside them), only the actual typeface changes.
        display: ['Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['Inter', 'sans-serif'],
      },
      keyframes: {
        'trace-in': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-line': {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'float-in': {
          '0%': { opacity: '0', transform: 'translateY(18px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
      },
      animation: {
        'trace-in': 'trace-in 0.4s ease-out forwards',
        'pulse-line': 'pulse-line 1.6s ease-in-out infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'float-in': 'float-in 0.55s cubic-bezier(0.16, 1, 0.3, 1) both',
        'shimmer': 'shimmer 1.8s linear infinite',
      },
    },
  },
  plugins: [],
}
