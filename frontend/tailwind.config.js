/** Trace design system — "security operations center / mission control".
 *  Near-black base, one electric-cyan accent, amber/red/green for states.
 *
 *  v0.5 — elevated for a premium, professional feel: a deeper layered
 *  near-black palette, a full accent scale, refined glow/elevation shadows,
 *  glass + gradient surfaces, and a richer ambient background. All token
 *  NAMES from the previous system are preserved so existing markup keeps
 *  working; only values are refined and new tokens are added.
 */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Base surfaces (near-black, layered from deepest to highest)
        base: "#05070b",
        surface: "#0a0e15",
        panel: "#0d121b",
        elevated: "#121925",
        line: "#1b2531",
        "line-soft": "#141c27",
        // Text
        ink: "#e9eff7",
        muted: "#8b98aa",
        faint: "#54606f",
        // The ONE electric accent (now a full scale) + state colors
        accent: {
          DEFAULT: "#27dcf2", // electric cyan — secure / active
          50: "#eafdff",
          100: "#c9f7fd",
          200: "#94eefb",
          300: "#54e0f5",
          400: "#27dcf2",
          500: "#10bcd6",
          600: "#0c97ad",
          soft: "#0e3a44",
          deep: "#062228",
        },
        warn: "#f7b733", // amber — pending / warning
        danger: "#ff4d6d", // red — denied / breach
        verify: "#3ed598", // muted green — verified
        royal: "#7c83ff", // secondary accent for investigator/forensics
      },
      fontFamily: {
        sans: ["Space Grotesk", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        xl: "0.85rem",
        "2xl": "1.1rem",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(39,220,242,0.22), 0 0 26px -6px rgba(39,220,242,0.5)",
        "glow-sm": "0 0 0 1px rgba(39,220,242,0.18), 0 0 14px -6px rgba(39,220,242,0.4)",
        "glow-warn": "0 0 0 1px rgba(247,183,51,0.24), 0 0 24px -6px rgba(247,183,51,0.42)",
        "glow-danger": "0 0 0 1px rgba(255,77,109,0.3), 0 0 26px -6px rgba(255,77,109,0.48)",
        "glow-verify": "0 0 0 1px rgba(62,213,152,0.24), 0 0 24px -6px rgba(62,213,152,0.42)",
        inset: "inset 0 1px 0 0 rgba(255,255,255,0.045)",
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 18px 40px -24px rgba(0,0,0,0.9)",
        lift: "0 24px 60px -28px rgba(0,0,0,0.95), 0 1px 0 0 rgba(255,255,255,0.05) inset",
      },
      backgroundImage: {
        // Faint telemetry grid texture
        grid: "linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)",
        "radial-fade":
          "radial-gradient(1200px 600px at 50% -10%, rgba(39,220,242,0.08), transparent 70%)",
        // Premium ambient aurora for splash/hero areas
        aurora:
          "radial-gradient(900px 500px at 12% -10%, rgba(39,220,242,0.10), transparent 60%), radial-gradient(800px 500px at 100% 0%, rgba(124,131,255,0.09), transparent 55%), radial-gradient(700px 500px at 50% 120%, rgba(62,213,152,0.05), transparent 60%)",
        "accent-sheen":
          "linear-gradient(135deg, rgba(39,220,242,0.16), rgba(39,220,242,0.02) 45%, transparent 70%)",
        "panel-sheen":
          "linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0) 38%)",
      },
      backgroundSize: {
        grid: "34px 34px",
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
        sweep: {
          "0%": { transform: "translateX(-120%)" },
          "100%": { transform: "translateX(120%)" },
        },
        floatUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        ring: {
          "0%": { transform: "scale(0.8)", opacity: "0.7" },
          "100%": { transform: "scale(2.2)", opacity: "0" },
        },
      },
      animation: {
        pulseLight: "pulseLight 1.6s ease-in-out infinite",
        scan: "scan 3.2s linear infinite",
        flicker: "flicker 2.5s ease-in-out infinite",
        sweep: "sweep 2.4s ease-in-out infinite",
        floatUp: "floatUp 0.5s ease-out both",
        ring: "ring 2.2s ease-out infinite",
      },
    },
  },
  plugins: [],
};
