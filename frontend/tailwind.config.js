/** Trace design system — "security operations center / mission control".
 *  Near-black base, one electric-cyan accent, amber/red/green for states.
 */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Base surfaces (near-black, layered)
        base: "#06080c",
        surface: "#0b0f16",
        panel: "#0e131c",
        elevated: "#131a25",
        line: "#1c2530",
        // Text
        ink: "#e6edf6",
        muted: "#8a97a8",
        faint: "#56616f",
        // The ONE electric accent + state colors
        accent: {
          DEFAULT: "#22d8f0", // electric cyan — secure / active
          soft: "#0e3a44",
          deep: "#072329",
        },
        warn: "#f5b13d", // amber — pending / warning
        danger: "#ff5470", // red — denied / breach
        verify: "#46c08a", // muted green — verified
      },
      fontFamily: {
        sans: ["Space Grotesk", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(34,216,240,0.25), 0 0 22px -4px rgba(34,216,240,0.45)",
        "glow-warn": "0 0 0 1px rgba(245,177,61,0.25), 0 0 22px -6px rgba(245,177,61,0.4)",
        "glow-danger": "0 0 0 1px rgba(255,84,112,0.3), 0 0 24px -6px rgba(255,84,112,0.45)",
        "glow-verify": "0 0 0 1px rgba(70,192,138,0.25), 0 0 22px -6px rgba(70,192,138,0.4)",
        inset: "inset 0 1px 0 0 rgba(255,255,255,0.04)",
      },
      backgroundImage: {
        // Faint telemetry grid texture
        grid: "linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)",
        "radial-fade":
          "radial-gradient(1200px 600px at 50% -10%, rgba(34,216,240,0.07), transparent 70%)",
      },
      backgroundSize: {
        grid: "32px 32px",
      },
      keyframes: {
        pulseLight: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        flicker: {
          "0%, 100%": { opacity: "0.9" },
          "50%": { opacity: "0.6" },
        },
      },
      animation: {
        pulseLight: "pulseLight 1.6s ease-in-out infinite",
        scan: "scan 3s linear infinite",
        flicker: "flicker 2.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
