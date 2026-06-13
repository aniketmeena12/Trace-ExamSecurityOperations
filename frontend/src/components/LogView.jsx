// Terminal-style audit log rendered as a visible SHA-256 hash chain.
import { motion } from "framer-motion";
import { StatusLight } from "./primitives";
import { Icon } from "./Icon";

// Map backend audit actions to a tone + icon for quick scanning.
const ACTION_META = {
  LOGIN: { tone: "idle", icon: "arrowRight" },
  EXAM_SEALED: { tone: "secure", icon: "lock" },
  SHARE_SUBMITTED: { tone: "pending", icon: "key" },
  UNLOCK_DENIED: { tone: "denied", icon: "x" },
  PAPER_UNLOCKED: { tone: "secure", icon: "unlock" },
  PAPER_ACCESSED: { tone: "idle", icon: "file" },
  WATERMARK_ISSUED: { tone: "secure", icon: "fingerprint" },
  LEAK_TRACED: { tone: "denied", icon: "crosshair" },
  AUDIT_VERIFIED: { tone: "verified", icon: "shieldCheck" },
};

function short(hash, n = 10) {
  if (!hash) return "—";
  return hash.length > n * 2 ? `${hash.slice(0, n)}…${hash.slice(-6)}` : hash;
}

export function LogView({ events = [], brokenIds = [], maxHeight = "26rem" }) {
  const broken = new Set(brokenIds);
  return (
    <div
      className="scroll-thin overflow-y-auto rounded-xl border border-line bg-base/70"
      style={{ maxHeight }}
    >
      <div className="divide-y divide-line/60">
        {events.length === 0 && (
          <div className="px-4 py-6 text-center text-xs text-faint">
            no events yet
          </div>
        )}
        {events.map((ev) => {
          const meta = ACTION_META[ev.action] || { tone: "idle", icon: "dot" };
          const isBroken = broken.has(ev.id);
          return (
            <motion.div
              key={ev.id}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              className={`grid grid-cols-[auto_1fr] gap-3 px-3 py-2.5 text-xs ${
                isBroken ? "bg-danger/10" : "hover:bg-white/[0.015]"
              }`}
            >
              <div className="flex items-center gap-2 pt-0.5">
                <span className="mono w-6 text-right text-faint">{ev.id}</span>
                <StatusLight tone={isBroken ? "denied" : meta.tone} />
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-x-2">
                  <Icon
                    name={meta.icon}
                    size={13}
                    className={isBroken ? "text-danger" : "text-faint"}
                  />
                  <span
                    className={`font-semibold ${
                      isBroken ? "text-danger" : "text-ink"
                    }`}
                  >
                    {ev.action}
                  </span>
                  <span className="text-muted">·</span>
                  <span className="mono text-accent">{ev.actor}</span>
                  {ev.target && (
                    <>
                      <span className="text-muted">·</span>
                      <span className="mono text-muted">{ev.target}</span>
                    </>
                  )}
                  <span className="mono ml-auto text-faint">
                    {ev.timestamp?.slice(11, 19)}
                  </span>
                </div>
                <div className="mt-1 flex items-center gap-1 text-faint">
                  <span className="mono text-[10px] text-faint/70">
                    prev {short(ev.prev_hash, 8)}
                  </span>
                  <Icon name="arrowRight" size={10} className="text-faint/50" />
                  <span
                    className={`mono text-[10px] ${
                      isBroken ? "text-danger" : "text-verify/70"
                    }`}
                  >
                    {short(ev.hash, 8)}
                  </span>
                  {isBroken && (
                    <span className="ml-2 rounded bg-danger/20 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-danger">
                      chain broken
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
