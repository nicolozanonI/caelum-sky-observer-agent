/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark Cosmic Theme
        primary: {
          50: '#f0f2ff',
          100: '#0a0a1a',       // Blu notte profondo (background)
          200: '#12122a',      // Antracite
          300: '#1a1a3a',      // Blu scuro
          400: '#252550',
          DEFAULT: '#0a0a1a',
        },
        secondary: {
          DEFAULT: '#12122a',
        },
        accent: {
          primary: '#4f8ef7',   // Blu luminoso (corpi celesti)
          secondary: '#8e44ad', // Viola (stelle)
          gold: '#ffd700',      // Oro (pulsanti)
          star: '#f5f5f5',      // Bianco stelle
        },
        text: {
          primary: '#e0e0e0',
          secondary: '#a0a0b0',
          muted: '#6b7280',
        },
        // Custom colors for celestial bodies
        celestial: {
          planet: '#4f8ef7',
          star: '#ffd700',
          deep_sky: '#8e44ad',
          constellation: '#00d4ff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      backgroundImage: {
        'cosmic-gradient': 'radial-gradient(ellipse at bottom, #1B2735 0%, #090A0F 100%)',
        'stars': "url('/src/assets/stars.png')",
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'orbit': 'orbit 20s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        orbit: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
    },
  },
  plugins: [],
}
