/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        display: ['"Syne"', 'sans-serif'],
      },
      colors: {
        drift: {
          bg: '#0F1117',
          surface: '#1A1D27',
          border: '#2A2D3A',
          muted: '#3A3D4A',
          text: '#E8EAF0',
          subtle: '#8B8FA8',
          accent: '#6C8EFF',
          danger: '#FF5C5C',
          warn: '#FFB347',
          ok: '#52D68A',
        }
      }
    }
  },
  plugins: []
}
