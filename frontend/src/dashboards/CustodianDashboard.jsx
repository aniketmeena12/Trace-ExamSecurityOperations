import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Button,
  Card,
  MonoReadout,
  SectionLabel,
  StatusPill,
} from "../components/primitives";
import { PageHeader } from "../components/PageHeader";
import { Icon } from "../components/Icon";
import { CountdownTimer } from "../components/CountdownTimer";
import { ShareSlots } from "../components/ShareSlots";
import { VaultState } from "../components/VaultState";
import { useAuth } from "../auth/AuthContext";
import { useExams, useMyShare, useSubmitShare, useUnlockStatus } from "../api/hooks";

function MaskedShare() {
  // A redacted stand-in for the share bytes until the window opens.
  return (
    <div className="rounded-md border border-line bg-base/60 px-2.5 py-1.5">
      <div className="flex flex-wrap gap-1">
        {Array.from({ length: 24 }).map((_, i) => (
          <span
            key={i}
            className="h-2.5 w-2.5 rounded-[2px] bg-line"
            style={{ opacity: 0.5 + ((i * 7) % 5) / 10 }}
          />
        ))}
      </div>
    </div>
  );
}

function ShareCard({ examId }) {
  const { data: share, error } = useMyShare(examId);
  const submit = useSubmitShare(examId);

  if (error) {
    return (
      <Card title="Your Key Share" icon="key" tone="idle">
        <p className="text-sm text-muted">You are not a custodian for this exam.</p>
      </Card>
    );
  }
  if (!share) {
    return (
      <Card title="Your Key Share" icon="key">
        <p className="text-sm text-faint">Loading…</p>
      </Card>
    );
  }

  const revealed = share.window_open && share.share;

  return (
    <Card
      title="Your Key Share"
      subtitle="one point on the secret polynomial — useless alone"
      icon="key"
      iconTone={revealed ? "secure" : "pending"}
      tone={revealed ? "secure" : "pending"}
      right={
        <StatusPill tone={share.masked ? "pending" : "secure"}>
          {share.masked ? "masked" : "revealed"}
        </StatusPill>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-[auto_1fr] gap-4">
          <MonoReadout label="x-coord" value={share.x} tone="accent" />
          <div className="flex flex-col gap-1">
            <span className="kicker">share f(x)</span>
            {revealed ? (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <MonoReadout value={share.share} tone="accent" />
              </motion.div>
            ) : (
              <MaskedShare />
            )}
          </div>
        </div>

        {share.masked ? (
          <div className="flex items-center justify-between gap-3 rounded-xl border border-warn/20 bg-warn/5 px-3 py-2.5">
            <span className="flex items-center gap-2 text-xs text-warn">
              <Icon name="lock" size={14} />
              Share sealed until the exam release window opens
            </span>
            <CountdownTimer seconds={share.seconds_remaining} />
          </div>
        ) : (
          <div className="flex items-center justify-between gap-3 rounded-xl border border-line bg-base/40 px-3 py-2.5">
            <span className="text-xs text-muted">
              {share.submitted
                ? "You have authorized release of your share."
                : "Window open — you may authorize release."}
            </span>
            <Button
              tone={share.submitted ? "ghost" : "solid"}
              disabled={share.submitted}
              loading={submit.isPending}
              icon={share.submitted ? "check" : "key"}
              onClick={() => submit.mutate()}
            >
              {share.submitted ? "Share Submitted" : "Submit Share"}
            </Button>
          </div>
        )}
        {submit.isError && (
          <p className="text-xs text-danger">{submit.error.message}</p>
        )}
      </div>
    </Card>
  );
}

function VaultPanel({ examId }) {
  const { data: status } = useUnlockStatus(examId, { poll: true });
  if (!status) return null;
  const tone =
    status.status === "UNLOCKED"
      ? "secure"
      : status.time_locked
      ? "denied"
      : "pending";
  return (
    <Card
      title="Vault Status"
      subtitle="live · shared across all custodians"
      icon="shield"
      iconTone={tone}
      tone={tone}
      right={<StatusPill tone={tone}>{status.status}</StatusPill>}
    >
      <div className="flex flex-col gap-5">
        <VaultState
          status={status.status}
          timeLocked={status.time_locked}
          sharesSubmitted={status.shares_submitted}
          threshold={status.threshold_k}
        />
        <div>
          <SectionLabel>quorum</SectionLabel>
          <ShareSlots
            n={status.num_custodians_n}
            submitted={status.shares_submitted}
            threshold={status.threshold_k}
          />
        </div>
        {status.time_locked && (
          <div className="flex items-center justify-between gap-3 rounded-xl border border-line bg-base/40 px-3 py-2.5">
            <span className="flex items-center gap-2 text-xs text-muted">
              <Icon name="clock" size={14} className="text-warn" />
              Time gate releases in
            </span>
            <CountdownTimer seconds={status.seconds_remaining} />
          </div>
        )}
      </div>
    </Card>
  );
}

function ExamPicker({ examId, onSelect }) {
  const { data: exams } = useExams();
  return (
    <div className="flex flex-wrap gap-2">
      {(exams || []).map((e) => (
        <button
          key={e.id}
          onClick={() => onSelect(e.id)}
          className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
            e.id === examId
              ? "border-accent/40 bg-accent/5 text-accent"
              : "border-line text-muted hover:text-ink"
          }`}
        >
          {e.name} <span className="mono text-[11px] text-faint">#{e.id}</span>
        </button>
      ))}
      {(!exams || exams.length === 0) && (
        <span className="text-xs text-faint">no exams sealed yet</span>
      )}
    </div>
  );
}

export function CustodianDashboard() {
  const { active } = useAuth();
  const { data: exams } = useExams();
  const [examId, setExamId] = useState(null);

  useEffect(() => {
    if (examId == null && exams && exams.length) {
      setExamId(exams[exams.length - 1].id);
    }
  }, [exams, examId]);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon="users"
        title="Custodian Console"
        subtitle="You hold one of five key shares. Three are required to unseal — no single custodian can open the vault."
        right={<StatusPill tone="secure">{active?.username}</StatusPill>}
      />

      <ExamPicker examId={examId} onSelect={setExamId} />

      {examId ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ShareCard examId={examId} />
          <VaultPanel examId={examId} />
        </div>
      ) : (
        <Card title="Custodian Console" icon="users">
          <p className="text-sm text-faint">Waiting for an exam to be sealed.</p>
        </Card>
      )}
    </div>
  );
}
