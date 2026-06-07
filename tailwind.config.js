/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: "#030303",
        card: "rgba(12, 12, 14, 0.6)",
        "card-hover": "rgba(20, 20, 24, 0.8)",
        border: "rgba(245, 158, 11, 0.1)",
        "border-focus": "rgba(245, 158, 11, 0.4)",
        brand: {
          50: '#fefbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          50: '#fbbf24', // fallback
          500: '#f59e0b', // main amber
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
          950: '#451a03',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'amber-glow': '0 0 15px rgba(245, 158, 11, 0.15)',
        'amber-glow-strong': '0 0 25px rgba(245, 158, 11, 0.35)',
        'card-shadow': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glowPulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'slide-in': 'slideIn 0.3s ease-out forwards',
      },
      keyframes: {
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(245, 158, 11, 0.1)' },
          '50%': { boxShadow: '0 0 25px rgba(245, 158, 11, 0.3)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
