import { useEffect, useState } from "react";

// Counts down to a target time. `seconds` is the authoritative remaining value
// from the backend at mount; we tick locally and re-sync whenever the prop
// changes (e.g. on each unlock-status poll). onElapsed fires once at zero.
export function CountdownTimer({ seconds, onElapsed, className = "" }) {
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

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {parts.map((v, i) => (
        <div key={i} className="flex items-baseline gap-1">
          <span className="mono text-2xl font-bold tabular-nums text-ink">
            {pad(v)}
          </span>
          <span className="text-[10px] font-medium uppercase text-faint">
            {labels[i]}
          </span>
        </div>
      ))}
    </div>
  );
}
