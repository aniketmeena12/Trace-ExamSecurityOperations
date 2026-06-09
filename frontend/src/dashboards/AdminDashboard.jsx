import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  MonoReadout,
  SectionLabel,
  StatusPill,
} from "../components/primitives";
import { CountdownTimer } from "../components/CountdownTimer";
import { ShareSlots } from "../components/ShareSlots";
import { VaultState } from "../components/VaultState";
import { useCreateExam, useExams, useUnlockStatus } from "../api/hooks";

function Field({ label, children, hint }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[10px] font-medium uppercase tracking-widest text-faint">
        {label}
      </span>
      {children}
      {hint && <span className="text-[11px] text-faint">{hint}</span>}
    </label>
  );
}

const inputCls =
  "rounded-lg border border-line bg-base/70 px-3 py-2 text-sm text-ink outline-none focus:border-accent/50 focus:shadow-glow placeholder:text-faint";

const RELEASE_PRESETS = [
  { label: "Already open", value: -5 },
  { label: "+30 sec", value: 30 },
  { label: "+2 min", value: 120 },
  { label: "+1 hour", value: 3600 },
];

function SealForm({ onCreated }) {
  const create = useCreateExam();
  const [form, setForm] = useState({
    name: "PHY-2026-AM",
    subject: "Physics",
    center_id: "DEL-01",
    threshold_k: 3,
    release_offset_seconds: 30,
    paper_text: "",
  });
  const set = (k) => (e) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    const body = {
      name: form.name,
      subject: form.subject,
      center_id: form.center_id,
      threshold_k: Number(form.threshold_k),
      release_offset_seconds: Number(form.release_offset_seconds),
    };
    if (form.paper_text.trim()) body.paper_text = form.paper_text;
    const exam = await create.mutateAsync(body);
    onCreated(exam.id);
  };

  return (
    <Card title="Seal a New Exam" subtitle="encrypt · split key · distribute to custodians">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Exam name">
            <input className={inputCls} value={form.name} onChange={set("name")} />
          </Field>
          <Field label="Subject">
            <input className={inputCls} value={form.subject} onChange={set("subject")} />
          </Field>
          <Field label="Center ID">
            <input className={inputCls} value={form.center_id} onChange={set("center_id")} />
          </Field>
          <Field label="Threshold (k of 5)" hint="custodians required to unseal">
            <input
              type="number"
              min={1}
              max={5}
              className={inputCls}
              value={form.threshold_k}
              onChange={set("threshold_k")}
            />
          </Field>
        </div>

        <Field label="Release window">
          <div className="flex flex-wrap items-center gap-2">
            {RELEASE_PRESETS.map((p) => (
              <button
                type="button"
                key={p.label}
                onClick={() =>
                  setForm((f) => ({ ...f, release_offset_seconds: p.value }))
                }
                className={`rounded-lg border px-2.5 py-1 text-xs transition-colors ${
                  Number(form.release_offset_seconds) === p.value
                    ? "border-accent/50 bg-accent/10 text-accent"
                    : "border-line text-muted hover:text-ink"
                }`}
              >
                {p.label}
              </button>
            ))}
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                className={`${inputCls} w-24`}
                value={form.release_offset_seconds}
                onChange={set("release_offset_seconds")}
              />
              <span className="text-xs text-faint">sec from now</span>
            </div>
          </div>
        </Field>

        <Field label="Paper content" hint="leave blank to use the seeded sample paper">
          <textarea
            rows={4}
            className={`${inputCls} resize-none font-mono text-xs`}
            placeholder="(using seeded sample paper)"
            value={form.paper_text}
            onChange={set("paper_text")}
          />
        </Field>

        <div className="flex items-center justify-between">
          <span className="text-xs text-faint">
            key → AES-256-GCM · split 3-of-5 · escrowed to cust1…cust5
          </span>
          <Button type="submit" loading={create.isPending}>
            Seal & Distribute
          </Button>
        </div>
        {create.isError && (
          <p className="text-xs text-danger">{create.error.message}</p>
        )}
      </form>
    </Card>
  );
}

function StatusRow({ label, children }) {
  return (
    <div className="flex items-center justify-between border-b border-line/60 py-2.5 last:border-0">
      <span className="text-xs text-muted">{label}</span>
      {children}
    </div>
  );
}

function OpsPanel({ examId }) {
  const { data: status } = useUnlockStatus(examId, { poll: true });
  const { data: exams } = useExams();
  const exam = useMemo(
    () => exams?.find((e) => e.id === examId),
    [exams, examId]
  );

  if (!status || !exam) {
    return (
      <Card title="Live Operations">
        <p className="text-sm text-faint">Select or seal an exam to monitor.</p>
      </Card>
    );
  }

  const tone =
    status.status === "UNLOCKED"
      ? "secure"
      : status.time_locked
      ? "denied"
      : "pending";

  return (
    <Card
      title="Live Operations"
      subtitle={`${exam.name} · ${exam.subject}`}
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
          <SectionLabel>custodian shares</SectionLabel>
          <ShareSlots
            n={status.num_custodians_n}
            submitted={status.shares_submitted}
            threshold={status.threshold_k}
          />
        </div>

        <div>
          <SectionLabel>telemetry</SectionLabel>
          <StatusRow label="Paper encryption">
            <StatusPill tone="secure">AES-256-GCM ✓</StatusPill>
          </StatusRow>
          <StatusRow label="Shares distributed">
            <span className="mono text-sm text-accent">
              {status.num_custodians_n} / {status.num_custodians_n}
            </span>
          </StatusRow>
          <StatusRow label="Time gate">
            {status.time_locked ? (
              <CountdownTimer seconds={status.seconds_remaining} />
            ) : (
              <StatusPill tone="secure">open</StatusPill>
            )}
          </StatusRow>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <MonoReadout label="exam id" value={`#${exam.id}`} tone="accent" />
          <MonoReadout
            label="threshold"
            value={`${status.threshold_k}-of-${status.num_custodians_n}`}
          />
          <MonoReadout
            label="release time (UTC)"
            value={status.release_time.slice(0, 19).replace("T", " ")}
            tone="muted"
            truncate
          />
          <MonoReadout
            label="unlocked at"
            value={status.unlocked_at ? status.unlocked_at.slice(11, 19) : "—"}
            tone={status.unlocked_at ? "verify" : "muted"}
          />
        </div>
      </div>
    </Card>
  );
}

function ExamList({ examId, onSelect }) {
  const { data: exams } = useExams();
  return (
    <Card title="Exams" subtitle={`${exams?.length || 0} sealed`}>
      <div className="flex flex-col gap-1.5">
        {(exams || []).map((e) => (
          <button
            key={e.id}
            onClick={() => onSelect(e.id)}
            className={`flex items-center justify-between rounded-lg border px-3 py-2 text-left transition-colors ${
              e.id === examId
                ? "border-accent/40 bg-accent/5"
                : "border-line hover:border-faint"
            }`}
          >
            <div>
              <div className="text-sm font-medium text-ink">{e.name}</div>
              <div className="mono text-[11px] text-faint">
                #{e.id} · {e.center_id}
              </div>
            </div>
            <StatusPill tone={e.status === "UNLOCKED" ? "secure" : "denied"}>
              {e.status}
            </StatusPill>
          </button>
        ))}
        {(!exams || exams.length === 0) && (
          <p className="py-3 text-center text-xs text-faint">
            no exams sealed yet
          </p>
        )}
      </div>
    </Card>
  );
}

export function AdminDashboard() {
  const { data: exams } = useExams();
  const [examId, setExamId] = useState(null);

  // Auto-select the most recent exam if none chosen.
  useEffect(() => {
    if (examId == null && exams && exams.length) {
      setExamId(exams[exams.length - 1].id);
    }
  }, [exams, examId]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-bold text-ink">Control Room</h1>
          <p className="text-sm text-muted">
            Seal exams, distribute key shares, and monitor the vault in real time.
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="flex flex-col gap-6">
          <SealForm onCreated={setExamId} />
          <ExamList examId={examId} onSelect={setExamId} />
        </div>
        <OpsPanel examId={examId} />
      </div>
    </div>
  );
}
