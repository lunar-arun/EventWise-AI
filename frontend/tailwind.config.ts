import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        mario: {
          sky: "#8EDBFA",
          red: "#E8483F",
          green: "#279B52",
          gold: "#FFC928",
          white: "#FFFFFF",
          navy: "#20304A",
          bg: "#F4FAFF",
          muted: "#64748B",
        },
      },
      boxShadow: {
        retro: "0 4px 0 0 #20304A",
        "retro-sm": "0 2px 0 0 #20304A",
        "retro-gold": "0 4px 0 0 #B78400",
      },
    },
  },
  plugins: [],
};

export default config;
