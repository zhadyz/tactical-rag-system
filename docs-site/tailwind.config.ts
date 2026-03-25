import type { Config } from 'tailwindcss'
import typography from '@tailwindcss/typography'

const config: Config = {
  content: [
    './pages/**/*.{js,jsx,ts,tsx,md,mdx}',
    './components/**/*.{js,jsx,ts,tsx}',
    './theme.config.tsx'
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        forge: {
          bg: '#050507',
          surface: '#0a0a10',
          'surface-2': '#111118',
          'surface-3': '#18181f',
          border: 'rgba(255, 255, 255, 0.06)',
        },
        primary: {
          50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd',
          400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8',
          800: '#1e40af', 900: '#1e3a8a', 950: '#172554'
        },
        accent: {
          50: '#f0fdf4', 100: '#dcfce7', 200: '#bbf7d0', 300: '#86efac',
          400: '#4ade80', 500: '#22c55e', 600: '#10b981', 700: '#15803d',
          800: '#166534', 900: '#14532d', 950: '#052e16'
        }
      },
      fontFamily: {
        display: ['Instrument Serif', 'Georgia', 'serif'],
        sans: ['Plus Jakarta Sans', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'Monaco', 'Consolas', 'monospace'],
      },
      fontSize: {
        'display-xl': ['clamp(3.5rem, 8vw, 7rem)', { lineHeight: '1', letterSpacing: '-0.02em' }],
        'display-lg': ['clamp(2.5rem, 5vw, 4.5rem)', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display-md': ['clamp(2rem, 4vw, 3rem)', { lineHeight: '1.15', letterSpacing: '-0.01em' }],
      },
      spacing: {
        '18': '4.5rem', '88': '22rem', '100': '25rem', '112': '28rem', '128': '32rem'
      },
      borderRadius: {
        '4xl': '2rem',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: '75ch',
            a: { color: '#60a5fa', '&:hover': { color: '#93c5fd' } },
            code: {
              color: '#60a5fa', backgroundColor: 'rgba(59, 130, 246, 0.1)',
              padding: '0.2em 0.4em', borderRadius: '0.25rem', fontWeight: '500'
            },
            'code::before': { content: '""' },
            'code::after': { content: '""' },
          }
        }
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        'slide-up': {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.8)', opacity: '1' },
          '100%': { transform: 'scale(2)', opacity: '0' }
        },
      },
      animation: {
        'fade-up': 'fade-up 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-in': 'fade-in 0.6s ease-out forwards',
        'slide-up': 'slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        shimmer: 'shimmer 2s linear infinite',
        'pulse-ring': 'pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    }
  },
  plugins: [typography]
}

export default config
