import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        // Sport-type accent colors
        run: { DEFAULT: "#22c55e", muted: "#166534" },
        lift: { DEFAULT: "#3b82f6", muted: "#1e3a8a" },
        mobility: { DEFAULT: "#a855f7", muted: "#581c87" },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      screens: {
        xs: "375px",
        sm: "640px",
        md: "768px",    // tablet — sidebar nav appears
        lg: "1024px",   // desktop — full dashboard
        xl: "1280px",
      },
      animation: {
        "pulse-rest": "pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-up": "slideUp 0.35s cubic-bezier(0.32, 0.72, 0, 1)",
        "fade-in": "fadeIn 0.2s ease-out",
        "shimmer": "shimmer 1.5s infinite linear",
      },
      keyframes: {
        slideUp: {
          from: { transform: "translateY(100%)" },
          to: { transform: "translateY(0)" },
        },
        fadeIn: {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          from: { backgroundPosition: "200% 0" },
          to: { backgroundPosition: "-200% 0" },
        },
      },
      spacing: {
        "bottom-nav": "4rem",    // height of the bottom nav bar
        "safe-bottom": "env(safe-area-inset-bottom, 0px)",
      },
    },
  },
  plugins: [],
};

export default config;
