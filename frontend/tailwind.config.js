/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#10161B',
          light: '#18212A',
          border: '#26323C',
        },
        paper: {
          DEFAULT: '#F6F1E4',
          dim: '#EDE6D3',
          text: '#23201A',
        },
        verdigris: {
          DEFAULT: '#3C8577',
          soft: '#5FA396',
        },
        brass: {
          DEFAULT: '#D9A441',
          soft: '#E6BD6E',
        },
        rust: {
          DEFAULT: '#B0503A',
          soft: '#C77258',
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
        sans: ['"Inter"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
