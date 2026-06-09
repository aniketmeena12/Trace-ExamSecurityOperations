// Core design-system primitives for the "mission control" look.
import { motion } from "framer-motion";

// ---------------------------------------------------------------- StatusLight
// A small pulsing telemetry dot.
export function StatusLight({ tone = "idle", pulse = false, className = "" }) {
  const map = {
    idle: "bg-faint",
    secure: "bg-accent shadow-[0_0_10px_2px_rgba(34,216,240,0.6)]",
    pending: "bg-warn shadow-[0_0_10px_2px_rgba(245,177,61,0.55)]",
    denied: "bg-danger shadow-[0_0_10px_2px_rgba(255,84,112,0.6)]",
    verified: "bg-verify shadow-[0_0_10px_2px_rgba(70,192,138,0.55)]",
  };
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${map[tone] || map.idle} ${
        pulse ? "animate-pulseLight" : ""
      } ${className}`}
    />
  );
}

// ------------------------------------------------------------------ StatusPill
const PILL = {
  idle: "text-faint border-line bg-white/[0.02]",
  secure: "text-accent border-accent/30 bg-accent/5",
  pending: "text-warn border-warn/30 bg-warn/5",
  denied: "text-danger border-danger/30 bg-danger/5",
  verified: "text-verify border-verify/30 bg-verify/5",
};
export function StatusPill({ tone = "idle", pulse = false, children }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-medium uppercase tracking-wider ${
        PILL[tone] || PILL.idle
      }`}
    >
      <StatusLight tone={tone} pulse={pulse} />
      {children}
    </span>
  );
}

// ------------------------------------------------------------------------ Card
export function Card({ title, subtitle, right, tone, children, className = "" }) {
  const glow =
    tone === "secure"
      ? "shadow-glow"
      : tone === "pending"
      ? "shadow-glow-warn"
      : tone === "denied"
      ? "shadow-glow-danger"
      : tone === "verified"
      ? "shadow-glow-verify"
      : "shadow-inset";
  return (
    <section
      className={`relative rounded-xl border border-line bg-panel/80 backdrop-blur-sm ${glow} ${className}`}
    >
      {(title || right) && (
        <header className="flex items-center justify-between border-b border-line px-4 py-3">
          <div>
            {title && (
              <h3 className="text-sm font-semibold tracking-wide text-ink">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="mt-0.5 text-xs text-muted">{subtitle}</p>
            )}
          </div>
          {right}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

// ------------------------------------------------------------------ MonoReadout
// Monospace technical readout for hashes / shares / IDs / timestamps.
export function MonoReadout({ label, value, tone = "default", truncate = false, title }) {
  const toneClass = {
    default: "text-ink",
    accent: "text-accent",
    warn: "text-warn",
    danger: "text-danger",
    verify: "text-verify",
    muted: "text-muted",
  }[tone];
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <span className="text-[10px] font-medium uppercase tracking-widest text-faint">
          {label}
        </span>
      )}
      <code
        title={title || (typeof value === "string" ? value : undefined)}
        className={`mono rounded-md border border-line bg-base/60 px-2.5 py-1.5 text-xs ${toneClass} ${
          truncate ? "block overflow-hidden text-ellipsis whitespace-nowrap" : "break-all"
        }`}
      >
        {value}
      </code>
    </div>
  );
}

// --------------------------------------------------------------------- Button
export function Button({ tone = "accent", disabled, loading, children, ...rest }) {
  const tones = {
    accent:
      "border-accent/40 text-accent hover:bg-accent/10 hover:shadow-glow disabled:opacity-40",
    ghost: "border-line text-muted hover:text-ink hover:border-faint",
    danger:
      "border-danger/40 text-danger hover:bg-danger/10 hover:shadow-glow-danger",
    verify:
      "border-verify/40 text-verify hover:bg-verify/10 hover:shadow-glow-verify",
  };
  return (
    <motion.button
      whileTap={{ scale: disabled ? 1 : 0.97 }}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg border px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed ${tones[tone]}`}
      {...rest}
    >
      {loading && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </motion.button>
  );
}

// ------------------------------------------------------------------- SectionLabel
export function SectionLabel({ children }) {
  return (
    <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-faint">
      <span className="h-px w-4 bg-line" />
      {children}
    </div>
  );
}
