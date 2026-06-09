import { useAuth } from "./auth/AuthContext";
import { RoleSwitcher } from "./components/RoleSwitcher";
import { StatusLight, StatusPill } from "./components/primitives";
import { AdminDashboard } from "./dashboards/AdminDashboard";
import { CustodianDashboard } from "./dashboards/CustodianDashboard";
import { CandidateDashboard } from "./dashboards/CandidateDashboard";
import { InvestigatorDashboard } from "./dashboards/InvestigatorDashboard";

function Header() {
  const { active } = useAuth();
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-accent/40 bg-accent/10 text-accent shadow-glow">
            <span className="mono text-lg font-bold">T</span>
          </div>
          <div className="leading-tight">
            <div className="text-sm font-bold tracking-[0.25em] text-ink">
              TRACE
            </div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-faint">
              Exam Security Ops
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-2 sm:flex">
            <StatusLight tone="secure" pulse />
            <span className="text-xs text-muted">backend live</span>
          </div>
          {active && (
            <div className="flex items-center gap-3 rounded-lg border border-line bg-panel px-3 py-1.5">
              <div className="text-right leading-tight">
                <div className="text-xs font-semibold text-ink">
                  {active.me?.display_name || active.username}
                </div>
                <div className="mono text-[10px] text-faint">
                  {active.username}
                </div>
              </div>
              <StatusPill tone="secure">{active.role}</StatusPill>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

function Splash({ message, tone = "secure", detail }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-radial-fade">
      <div className="flex items-center gap-3">
        <StatusLight tone={tone} pulse />
        <span className="text-lg font-semibold tracking-wide text-ink">
          {message}
        </span>
      </div>
      {detail && (
        <p className="max-w-md text-center text-sm text-muted">{detail}</p>
      )}
    </div>
  );
}

export default function App() {
  const { status, role, error } = useAuth();

  if (status === "connecting") {
    return <Splash message="Establishing secure session…" />;
  }
  if (status === "error") {
    return (
      <Splash
        tone="denied"
        message="Cannot reach Trace backend"
        detail={
          "Start the API first:  cd backend && uvicorn trace.api.app:app --reload  " +
          `(${error?.message || "connection failed"})`
        }
      />
    );
  }

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
      </main>
      <RoleSwitcher />
    </div>
  );
}
