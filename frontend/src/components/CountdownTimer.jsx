import { useEffect, useState } from "react";

// Counts down to a target time. `seconds` is the authoritative remaining value
// from the backend at mount; we tick locally and re-sync whenever the prop
// changes (e.g. on each unlock-status poll). onElapsed fires once at zero.
export function CountdownTimer({ seconds, onElapsed, size = "md", className = "" }) {
  const [remaining, setRemaining] = useState(Math.max(0, seconds ?? 0));

  useEffect(() => {
    setRemaining(Math.max(0, seconds ?? 0));
  }, [seconds]);

  useEffect(() => {
    if (remaining <= 0) {
      onElapsed?.();
      return;
    }
    const t = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(t);
          onElapsed?.();
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seconds]);

  const d = Math.floor(remaining / 86400);
  const h = Math.floor((remaining % 86400) / 3600);
  const m = Math.floor((remaining % 3600) / 60);
  const s = Math.floor(remaining % 60);
  const pad = (n) => String(n).padStart(2, "0");
  const parts = d > 0 ? [d, h, m, s] : [h, m, s];
  const labels = d > 0 ? ["D", "H", "M", "S"] : ["H", "M", "S"];

  const digitCls =
    size === "lg" ? "text-3xl px-2.5 py-1.5" : "text-xl px-2 py-1";

  return (
    <div className={`flex items-center gap-1.5 ${className}`}>
      {parts.map((v, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <div className="flex flex-col items-center gap-1">
            <span
              className={`mono rounded-md border border-line bg-base/70 font-bold tabular text-ink shadow-inset ${digitCls}`}
            >
              {pad(v)}
            </span>
            <span className="text-[9px] font-medium uppercase tracking-wider text-faint">
              {labels[i]}
            </span>
          </div>
          {i < parts.length - 1 && (
            <span className="mono -mt-3 text-lg font-bold text-faint">:</span>
          )}
        </div>
      ))}
    </div>
  );
}
