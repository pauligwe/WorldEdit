import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#f9f9f9",
          dim: "#dadada",
          bright: "#f9f9f9",
          lowest: "#ffffff",
          low: "#f3f3f3",
          container: "#eeeeee",
          high: "#e8e8e8",
          highest: "#e2e2e2",
        },
        on: {
          surface: "#1b1b1b",
          "surface-variant": "#4c4546",
          primary: "#ffffff",
        },
        outline: {
          DEFAULT: "#7e7576",
          variant: "#cfc4c5",
        },
        primary: {
          DEFAULT: "#000000",
          container: "#1b1b1b",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        DEFAULT: "0.25rem",
      },
      boxShadow: {
        soft: "0 4px 20px rgba(0, 0, 0, 0.04)",
      },
    },
  },
  plugins: [],
};
export default config;
