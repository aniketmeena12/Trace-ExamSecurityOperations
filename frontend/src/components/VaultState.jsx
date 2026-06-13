// Compact vault-state indicator. The cinematic time-lock vault is the M5 hero;
// here we present a clean, professional state badge. State is driven entirely
// by backend data:
//   SEALED + time_locked  -> sealed
//   SEALED + enough shares + open window -> unsealing (transient)
//   UNLOCKED -> open
import { motion } from "framer-motion";
import { StatusPill } from "./primitives";
import { Icon } from "./Icon";

export function VaultState({ status, timeLocked, sharesSubmitted, threshold }) {
  let state = "sealed";
  if (status === "UNLOCKED") state = "open";
  else if (!timeLocked && sharesSubmitted >= threshold) state = "unsealing";

  const cfg = {
    sealed: {
      tone: "denied",
      label: "Vault Sealed",
      icon: "lock",
      ring: "border-danger/40 text-danger",
    },
    unsealing: {
      tone: "pending",
      label: "Unsealing",
      icon: "unlock",
      ring: "border-warn/50 text-warn",
    },
    open: {
      tone: "secure",
      label: "Vault Open",
      icon: "shieldCheck",
      ring: "border-accent/50 text-accent",
    },
  }[state];

  return (
    <div className="flex items-center gap-4">
      <motion.div
        animate={
          state === "unsealing"
            ? {
                boxShadow: [
                  "0 0 0px rgba(247,183,51,0.2)",
                  "0 0 28px rgba(247,183,51,0.5)",
                  "0 0 0px rgba(247,183,51,0.2)",
                ],
              }
            : {}
        }
        transition={{ repeat: Infinity, duration: 1.8 }}
        className={`flex h-14 w-14 items-center justify-center rounded-2xl border bg-base/60 ${cfg.ring}`}
      >
        <Icon name={cfg.icon} size={26} strokeWidth={1.7} />
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
