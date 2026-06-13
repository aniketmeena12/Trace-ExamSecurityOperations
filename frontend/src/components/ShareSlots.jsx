// Visual indicator of custodian shares: n slots, `submitted` of them filled,
// with the threshold k marked. Drives the "2 of 3 required shares" readout.
import { motion } from "framer-motion";
import { Icon } from "./Icon";

export function ShareSlots({ n = 5, submitted = 0, threshold = 3 }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        {Array.from({ length: n }).map((_, i) => {
          const filled = i < submitted;
          const isThreshold = i + 1 === threshold;
          return (
            <motion.div
              key={i}
              initial={false}
              animate={{ scale: filled ? 1 : 0.92, opacity: filled ? 1 : 0.55 }}
              className={`relative flex h-10 w-10 items-center justify-center rounded-xl border ${
                filled
                  ? "border-accent/50 bg-accent/10 text-accent shadow-glow-sm"
                  : "border-line bg-base/60 text-faint"
              }`}
              title={`Custodian ${i + 1}`}
            >
              <Icon name="key" size={16} />
              {isThreshold && (
                <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[9px] font-semibold uppercase tracking-wide text-warn">
                  k={threshold}
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
      <div className="mt-4 text-xs text-muted">
        <span className="mono font-semibold text-accent">{submitted}</span> of{" "}
        <span className="mono font-semibold text-ink">{threshold}</span> required
        shares submitted
        <span className="text-faint"> · {n} custodians total</span>
      </div>
    </div>
  );
}
