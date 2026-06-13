// Core design-system primitives for the "mission control" look.
// v0.5 — premium pass: layered surfaces, gradient accent edges, an icon-aware
// Card, a solid primary Button, and new Metric / Brand / IconBadge atoms.
import { motion } from "framer-motion";
import { Icon } from "./Icon";

// Shared tone → color maps so every atom speaks the same visual language.
const TONE_TEXT = {
  idle: "text-faint",
  default: "text-ink",
  secure: "text-accent",
  accent: "text-accent",
  pending: "text-warn",
  warn: "text-warn",
  denied: "text-danger",
  danger: "text-danger",
  verified: "text-verify",
  verify: "text-verify",
  muted: "text-muted",
};

// ---------------------------------------------------------------- StatusLight
// A small pulsing telemetry dot.
export function StatusLight({ tone = "idle", pulse = false, className = "" }) {
  const map = {
    idle: "bg-faint",
    secure: "bg-accent shadow-[0_0_10px_2px_rgba(39,220,242,0.6)]",
    pending: "bg-warn shadow-[0_0_10px_2px_rgba(247,183,51,0.55)]",
    denied: "bg-danger shadow-[0_0_10px_2px_rgba(255,77,109,0.6)]",
    verified: "bg-verify shadow-[0_0_10px_2px_rgba(62,213,152,0.55)]",
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

// ------------------------------------------------------------------- IconBadge
// A rounded, tinted icon chip used in card headers and hero rows.
const BADGE = {
  idle: "border-line bg-white/[0.03] text-muted",
  secure: "border-accent/35 bg-accent/10 text-accent shadow-glow-sm",
  accent: "border-accent/35 bg-accent/10 text-accent shadow-glow-sm",
  pending: "border-warn/35 bg-warn/10 text-warn",
  denied: "border-danger/35 bg-danger/10 text-danger",
  verified: "border-verify/35 bg-verify/10 text-verify",
  royal: "border-royal/35 bg-royal/10 text-royal",
};
export function IconBadge({ icon, tone = "idle", size = "md" }) {
  const dim =
    size === "lg" ? "h-12 w-12" : size === "sm" ? "h-8 w-8" : "h-10 w-10";
  const iconSize = size === "lg" ? 22 : size === "sm" ? 16 : 18;
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-xl border ${dim} ${
        BADGE[tone] || BADGE.idle
      }`}
    >
      <Icon name={icon} size={iconSize} />
    </span>
  );
}

// ------------------------------------------------------------------------ Card
const EDGE = {
  secure: "before:bg-accent/70",
  pending: "before:bg-warn/70",
  denied: "before:bg-danger/70",
  verified: "before:bg-verify/70",
  royal: "before:bg-royal/70",
};
const GLOW = {
  secure: "shadow-glow",
  pending: "shadow-glow-warn",
  denied: "shadow-glow-danger",
  verified: "shadow-glow-verify",
};
export function Card({
  title,
  subtitle,
  icon,
  iconTone,
  right,
  tone,
  children,
  className = "",
}) {
  const edge = EDGE[tone];
  const glow = GLOW[tone] || "shadow-card";
  return (
    <section
      className={`group relative overflow-hidden rounded-2xl border border-line bg-panel/80 backdrop-blur-sm ${glow} ${
        edge
          ? `before:absolute before:inset-x-0 before:top-0 before:h-px before:content-[''] ${edge}`
          : ""
      } ${className}`}
    >
      {/* faint top-down sheen for depth */}
      <div className="pointer-events-none absolute inset-0 bg-panel-sheen opacity-60" />
      {(title || right) && (
        <header className="relative flex items-center justify-between gap-3 border-b border-line/80 px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            {icon && <IconBadge icon={icon} tone={iconTone || tone || "idle"} size="sm" />}
            <div className="min-w-0">
              {title && (
                <h3 className="truncate text-sm font-semibold tracking-wide text-ink">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="mt-0.5 truncate text-xs text-muted">{subtitle}</p>
              )}
            </div>
          </div>
          {right && <div className="shrink-0">{right}</div>}
        </header>
      )}
      <div className="relative p-4">{children}</div>
    </section>
  );
}

// ------------------------------------------------------------------ MonoReadout
// Monospace technical readout for hashes / shares / IDs / timestamps.
export function MonoReadout({ label, value, tone = "default", truncate = false, title }) {
  const toneClass = TONE_TEXT[tone] || TONE_TEXT.default;
  return (
    <div className="flex min-w-0 flex-col gap-1">
      {label && <span className="kicker">{label}</span>}
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

// ----------------------------------------------------------------------- Metric
// A compact stat block: big tabular value + label, optional icon and tone.
export function Metric({ label, value, sub, tone = "default", icon }) {
  const toneClass = TONE_TEXT[tone] || TONE_TEXT.default;
  return (
    <div className="relative flex flex-col gap-1 overflow-hidden rounded-xl border border-line bg-base/50 px-3.5 py-3">
      <div className="flex items-center justify-between">
        <span className="kicker">{label}</span>
        {icon && <Icon name={icon} size={14} className="text-faint" />}
      </div>
      <span className={`mono text-2xl font-bold tabular leading-none ${toneClass}`}>
        {value}
      </span>
      {sub && <span className="text-[11px] text-faint">{sub}</span>}
    </div>
  );
}

// --------------------------------------------------------------------- Button
export function Button({
  tone = "accent",
  size = "md",
  icon,
  iconRight,
  disabled,
  loading,
  children,
  className = "",
  ...rest
}) {
  const tones = {
    // Outline (default) variants
    accent:
      "border-accent/40 text-accent hover:bg-accent/10 hover:shadow-glow disabled:opacity-40",
    ghost: "border-line text-muted hover:text-ink hover:border-faint",
    danger:
      "border-danger/40 text-danger hover:bg-danger/10 hover:shadow-glow-danger",
    verify:
      "border-verify/40 text-verify hover:bg-verify/10 hover:shadow-glow-verify",
    // Solid primary — for the single most important CTA on a surface
    solid:
      "border-transparent bg-gradient-to-b from-accent-300 to-accent-500 text-base font-semibold shadow-glow hover:from-accent-200 hover:to-accent-400 disabled:opacity-40",
  };
  const sizes = {
    sm: "px-2.5 py-1.5 text-xs gap-1.5",
    md: "px-3.5 py-2 text-sm gap-2",
    lg: "px-5 py-2.5 text-sm gap-2",
  };
  return (
    <motion.button
      whileTap={{ scale: disabled ? 1 : 0.97 }}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center rounded-lg border font-medium transition-colors disabled:cursor-not-allowed ${tones[tone]} ${sizes[size]} ${className}`}
      {...rest}
    >
      {loading ? (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        icon && <Icon name={icon} size={size === "sm" ? 14 : 16} />
      )}
      {children}
      {iconRight && !loading && (
        <Icon name={iconRight} size={size === "sm" ? 14 : 16} />
      )}
    </motion.button>
  );
}

// ------------------------------------------------------------------- SectionLabel
export function SectionLabel({ children }) {
  return (
    <div className="mb-2.5 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-faint">
      <span className="h-px w-4 bg-gradient-to-r from-line to-transparent" />
      {children}
    </div>
  );
}

// ------------------------------------------------------------------------- Brand
// The Trace wordmark + shield mark. Used by the header and splash.
export function Brand({ size = "md" }) {
  const markDim = size === "lg" ? "h-11 w-11" : "h-9 w-9";
  const markIcon = size === "lg" ? 24 : 20;
  const title = size === "lg" ? "text-base" : "text-sm";
  return (
    <div className="flex items-center gap-3">
      <div
        className={`relative flex items-center justify-center rounded-xl border border-accent/40 bg-accent/10 text-accent shadow-glow ${markDim}`}
      >
        <Icon name="shieldCheck" size={markIcon} strokeWidth={1.8} />
        <span className="absolute inset-0 rounded-xl border border-accent/20 animate-pulseLight" />
      </div>
      <div className="leading-tight">
        <div className={`font-bold tracking-[0.3em] text-ink ${title}`}>TRACE</div>
        <div className="text-[10px] uppercase tracking-[0.3em] text-faint">
          Exam Security Ops
        </div>
      </div>
    </div>
  );
}

// Shared input class so forms look identical everywhere.
export const inputCls =
  "w-full rounded-lg border border-line bg-base/70 px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-accent/50 focus:shadow-glow-sm placeholder:text-faint";
