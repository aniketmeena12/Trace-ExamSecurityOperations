import { useAuth } from "./auth/AuthContext";
import { RoleSwitcher } from "./components/RoleSwitcher";
import { Brand, StatusLight, StatusPill } from "./components/primitives";
import { Icon, ROLE_ICON } from "./components/Icon";
import { AdminDashboard } from "./dashboards/AdminDashboard";
import { CustodianDashboard } from "./dashboards/CustodianDashboard";
import { CandidateDashboard } from "./dashboards/CandidateDashboard";
import { InvestigatorDashboard } from "./dashboards/InvestigatorDashboard";
import { motion } from "framer-motion";

function Header() {
  const { active } = useAuth();
  return (
    <header className="sticky top-0 z-40 border-b border-line glass">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <Brand />

        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-2 rounded-full border border-verify/25 bg-verify/5 px-3 py-1.5 sm:flex">
            <StatusLight tone="verified" pulse />
            <span className="text-xs font-medium text-verify">backend live</span>
          </div>
          {active && (
            <div className="flex items-center gap-3 rounded-xl border border-line bg-panel px-3 py-1.5 shadow-inset">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent">
                <Icon name={ROLE_ICON[active.role]} size={15} />
              </span>
              <div className="text-right leading-tight">
                <div className="text-xs font-semibold text-ink">
                  {active.me?.display_name || active.username}
                </div>
                <div className="mono text-[10px] text-faint">{active.username}</div>
              </div>
              <StatusPill tone="secure">{active.role}</StatusPill>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

// ── Premium boot splash: visualizes the REAL sequential auth against the
//    backend (each identity is a genuine JWT login) as a progress sweep.
function BootSplash() {
  const { sessions, identities } = useAuth();
  const ready = Object.keys(sessions).length;
  const total = identities.length;
  const pct = Math.round((ready / total) * 100);

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center gap-8 overflow-hidden bg-aurora px-6">
      <div className="telemetry-grid pointer-events-none absolute inset-0 bg-grid bg-grid opacity-40" />
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative flex flex-col items-center gap-6"
      >
        <div className="relative flex h-24 w-24 items-center justify-center">
          <span className="absolute inset-0 rounded-2xl border border-accent/30 animate-ring" />
          <span className="absolute inset-0 rounded-2xl border border-accent/20 animate-ring [animation-delay:.7s]" />
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl border border-accent/40 bg-accent/10 text-accent shadow-glow">
            <Icon name="shieldCheck" size={40} strokeWidth={1.6} />
          </div>
        </div>

        <div className="text-center">
          <div className="text-2xl font-bold tracking-[0.3em] text-ink">TRACE</div>
          <div className="mt-1 text-xs uppercase tracking-[0.32em] text-faint">
            Establishing secure session
          </div>
        </div>

        <div className="w-72">
          <div className="relative h-1.5 overflow-hidden rounded-full border border-line bg-base/70">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-accent-500 to-accent-300 shadow-glow-sm"
              animate={{ width: `${pct}%` }}
              transition={{ ease: "easeOut" }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-faint">
            <span className="mono">authenticating identities</span>
            <span className="mono text-accent">
              {ready}/{total}
            </span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function ErrorSplash({ error }) {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center gap-5 bg-aurora px-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-danger/40 bg-danger/10 text-danger shadow-glow-danger">
        <Icon name="alert" size={30} />
      </div>
      <div className="text-center">
        <div className="text-lg font-semibold text-ink">Cannot reach Trace backend</div>
        <p className="mt-2 max-w-md text-sm text-muted">
          Start the API first, then reload:
        </p>
      </div>
      <code className="mono rounded-lg border border-line bg-base/70 px-4 py-2 text-xs text-accent">
        cd backend && uvicorn trace.api.app:app --reload
      </code>
      <span className="text-xs text-faint">{error?.message || "connection failed"}</span>
    </div>
  );
}

const GUARANTEES = [
  { icon: "key", text: "Just-in-time multi-custodian decryption" },
  { icon: "fingerprint", text: "Per-candidate invisible watermark" },
  { icon: "hash", text: "Tamper-evident hash-chained audit log" },
];

function Footer() {
  return (
    <footer className="mx-auto mt-10 max-w-7xl px-6">
      <div className="rule mb-4" />
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          {GUARANTEES.map((g) => (
            <div key={g.text} className="flex items-center gap-2 text-xs text-muted">
              <Icon name={g.icon} size={15} className="text-accent" />
              {g.text}
            </div>
          ))}
        </div>
        <div className="mono text-[11px] text-faint">
          Trace · India's FAR AWAY 2026 · secure examinations
        </div>
      </div>
    </footer>
  );
}

export default function App() {
  const { status, role, error } = useAuth();

  if (status === "connecting") return <BootSplash />;
  if (status === "error") return <ErrorSplash error={error} />;

  const Dashboard =
    {
      admin: AdminDashboard,
      custodian: CustodianDashboard,
      candidate: CandidateDashboard,
      investigator: InvestigatorDashboard,
    }[role] || (() => null);

  return (
    <div className="min-h-screen pb-28">
      <Header />
      <main className="telemetry-grid">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <Dashboard />
        </div>
        <Footer />
      </main>
      <RoleSwitcher />
    </div>
  );
}
