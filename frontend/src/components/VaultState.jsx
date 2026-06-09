// Compact vault-state indicator. M4 keeps motion minimal; the cinematic
// time-lock vault is the M5 hero. State is driven entirely by backend data:
//   SEALED + time_locked  -> sealed
//   SEALED + enough shares + open window -> unsealing (transient)
//   UNLOCKED -> open
import { motion } from "framer-motion";
import { StatusPill } from "./primitives";

export function VaultState({ status, timeLocked, sharesSubmitted, threshold }) {
  let state = "sealed";
  if (status === "UNLOCKED") state = "open";
  else if (!timeLocked && sharesSubmitted >= threshold) state = "unsealing";

  const cfg = {
    sealed: { tone: "denied", label: "Vault Sealed", glyph: "🔒", ring: "border-danger/40" },
    unsealing: { tone: "pending", label: "Unsealing", glyph: "🔓", ring: "border-warn/50" },
    open: { tone: "secure", label: "Vault Open", glyph: "⬡", ring: "border-accent/50" },
  }[state];

  return (
    <div className="flex items-center gap-4">
      <motion.div
        animate={
          state === "unsealing"
            ? { boxShadow: ["0 0 0px rgba(245,177,61,0.2)", "0 0 26px rgba(245,177,61,0.5)", "0 0 0px rgba(245,177,61,0.2)"] }
            : {}
        }
        transition={{ repeat: Infinity, duration: 1.8 }}
        className={`flex h-14 w-14 items-center justify-center rounded-xl border bg-base/60 text-2xl ${cfg.ring}`}
      >
        {cfg.glyph}
      </motion.div>
      <div className="flex flex-col gap-1.5">
        <StatusPill tone={cfg.tone} pulse={state === "unsealing"}>
          {cfg.label}
        </StatusPill>
        <span className="text-xs text-muted">
          {state === "open"
            ? "key reconstructed · paper released"
            : state === "unsealing"
            ? "threshold met · awaiting reconstruction"
            : timeLocked
            ? "time-lock engaged"
            : "awaiting custodian shares"}
        </span>
      </div>
    </div>
  );
}
