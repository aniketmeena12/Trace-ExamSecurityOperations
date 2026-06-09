// Visual indicator of custodian shares: n slots, `submitted` of them filled,
// with the threshold k marked. Drives the "2 of 3 required shares" readout.
import { motion } from "framer-motion";

export function ShareSlots({ n = 5, submitted = 0, threshold = 3 }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        {Array.from({ length: n }).map((_, i) => {
          const filled = i < submitted;
          return (
            <motion.div
              key={i}
              initial={false}
              animate={{
                scale: filled ? 1 : 0.92,
                opacity: filled ? 1 : 0.5,
              }}
              className={`relative flex h-9 w-9 items-center justify-center rounded-md border text-xs font-semibold ${
                filled
                  ? "border-accent/50 bg-accent/10 text-accent shadow-glow"
                  : "border-line bg-base/60 text-faint"
              }`}
              title={`Custodian ${i + 1}`}
            >
              {filled ? "◆" : "◇"}
              {i + 1 === threshold && (
                <span className="absolute -bottom-5 text-[9px] font-medium uppercase tracking-wide text-warn">
                  k={threshold}
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
      <div className="mt-3 text-xs text-muted">
        <span className="mono text-accent">{submitted}</span> of{" "}
        <span className="mono text-ink">{threshold}</span> required shares
        submitted
        <span className="text-faint"> · {n} custodians total</span>
      </div>
    </div>
  );
}
