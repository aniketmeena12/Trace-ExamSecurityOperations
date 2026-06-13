// Floating demo utility: jump between all 4 role dashboards instantly.
// Every identity is pre-authenticated against the real backend.
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useAuth } from "../auth/AuthContext";
import { StatusLight } from "./primitives";
import { Icon, ROLE_ICON } from "./Icon";

const ROLE_ORDER = ["admin", "custodian", "candidate", "investigator"];
const ROLE_LABEL = {
  admin: "Admin",
  custodian: "Custodian",
  candidate: "Candidate",
  investigator: "Investigator",
};

export function RoleSwitcher() {
  const { identities, active, activeKey, setActiveKey } = useAuth();
  const [open, setOpen] = useState(true);
  const activeRole = active?.role;

  const byRole = (role) => identities.filter((i) => i.role === role);

  return (
    <div className="fixed bottom-5 left-1/2 z-50 -translate-x-1/2">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            className="mb-2 flex flex-col gap-2 rounded-2xl border border-line bg-surface/95 p-2 shadow-lift backdrop-blur-xl"
          >
            <div className="flex items-center gap-1.5">
              {ROLE_ORDER.map((role) => {
                const first = byRole(role)[0];
                const isActive = activeRole === role;
                return (
                  <button
                    key={role}
                    onClick={() => setActiveKey(first.key)}
                    className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium transition-all ${
                      isActive
                        ? "border-accent/50 bg-accent/10 text-accent shadow-glow"
                        : "border-line text-muted hover:border-faint hover:text-ink"
                    }`}
                  >
                    <Icon name={ROLE_ICON[role]} size={16} />
                    {ROLE_LABEL[role]}
                  </button>
                );
              })}
            </div>

            {/* Secondary selector when a role has multiple seeded accounts. */}
            {(activeRole === "custodian" || activeRole === "candidate") && (
              <div className="flex flex-wrap items-center gap-1.5 border-t border-line pt-2">
                <span className="px-1 text-[10px] uppercase tracking-widest text-faint">
                  identity
                </span>
                {byRole(activeRole).map((id) => (
                  <button
                    key={id.key}
                    onClick={() => setActiveKey(id.key)}
                    className={`rounded-lg border px-2.5 py-1 text-xs transition-colors ${
                      activeKey === id.key
                        ? "border-accent/50 bg-accent/10 text-accent"
                        : "border-line text-muted hover:text-ink"
                    }`}
                  >
                    <span className="mono">{id.username}</span>
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <button
        onClick={() => setOpen((o) => !o)}
        className="mx-auto flex items-center gap-2 rounded-full border border-line bg-surface/95 px-4 py-1.5 text-xs text-muted shadow-inset backdrop-blur-xl hover:text-ink"
      >
        <StatusLight tone="secure" pulse />
        <span className="font-medium uppercase tracking-[0.18em]">Demo</span>
        <span className="text-faint">·</span>
        role switcher
        <Icon name={open ? "chevronDown" : "chevronUp"} size={14} className="text-faint" />
      </button>
    </div>
  );
}
