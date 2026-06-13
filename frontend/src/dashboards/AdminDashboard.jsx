import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  Metric,
  MonoReadout,
  SectionLabel,
  StatusPill,
  inputCls,
} from "../components/primitives";
import { PageHeader } from "../components/PageHeader";
import { Icon } from "../components/Icon";
import { CountdownTimer } from "../components/CountdownTimer";
import { ShareSlots } from "../components/ShareSlots";
import { VaultState } from "../components/VaultState";
import {
  useBlueprint,
  useCreateExam,
  useExams,
  useQuestions,
  useUnlockStatus,
} from "../api/hooks";

// Matches the seeded MATH-DEMO bank (algebra-easy ×5, geometry-hard ×5).
const DEMO_BLUEPRINT = {
  sections: [
    { name: "A", topic: "algebra", difficulty: "easy", count: 3 },
    { name: "B", topic: "geometry", difficulty: "hard", count: 2 },
  ],
};

function Field({ label, children, hint }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="kicker">{label}</span>
      {children}
      {hint && <span className="text-[11px] text-faint">{hint}</span>}
    </label>
  );
}

const RELEASE_PRESETS = [
  { label: "Already open", value: -5 },
  { label: "+30 sec", value: 30 },
  { label: "+2 min", value: 120 },
  { label: "+1 hour", value: 3600 },
];

function ModeToggle({ mode, onChange }) {
  const opts = [
    { key: "static", label: "Static paper", icon: "lock" },
    { key: "dynamic", label: "Dynamic bank", icon: "layers" },
  ];
  return (
    <div className="flex gap-2">
      {opts.map((o) => (
        <button
          type="button"
          key={o.key}
          onClick={() => onChange(o.key)}
          className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg border px-3 py-2 text-xs transition-colors ${
            mode === o.key
              ? "border-accent/50 bg-accent/10 text-accent"
              : "border-line text-muted hover:text-ink"
          }`}
        >
          <Icon name={o.icon} size={13} />
          {o.label}
        </button>
      ))}
    </div>
  );
}

function SealForm({ onCreated }) {
  const create = useCreateExam();
  const [mode, setMode] = useState("static");
  const [form, setForm] = useState({
    name: "PHY-2026-AM",
    subject: "Physics",
    center_id: "DEL-01",
    threshold_k: 3,
    release_offset_seconds: 30,
    paper_text: "",
  });
  const [blueprintText, setBlueprintText] = useState(
    JSON.stringify(DEMO_BLUEPRINT, null, 2)
  );
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  // Switching to dynamic defaults the subject to the seeded demo bank.
  const pickMode = (m) => {
    setMode(m);
    if (m === "dynamic" && form.subject === "Physics") {
      setForm((f) => ({ ...f, subject: "MATH-DEMO", name: "MATH-2026-AM" }));
    }
  };

  const bankSubject = mode === "dynamic" ? form.subject : null;
  const { data: bank } = useQuestions(bankSubject);

  const submit = async (e) => {
    e.preventDefault();
    const body = {
      name: form.name,
      subject: form.subject,
      center_id: form.center_id,
      threshold_k: Number(form.threshold_k),
      release_offset_seconds: Number(form.release_offset_seconds),
      assembly_mode: mode,
    };
    if (mode === "dynamic") {
      try {
        body.blueprint = JSON.parse(blueprintText);
      } catch {
        create.reset?.();
        alert("Blueprint is not valid JSON.");
        return;
      }
    } else if (form.paper_text.trim()) {
      body.paper_text = form.paper_text;
    }
    const exam = await create.mutateAsync(body);
    onCreated(exam.id);
  };

  return (
    <Card
      title="Seal a New Exam"
      subtitle="encrypt · split key · distribute to custodians"
      icon="lock"
      iconTone="secure"
    >
      <form onSubmit={submit} className="flex flex-col gap-4">
        <ModeToggle mode={mode} onChange={pickMode} />

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

        {mode === "static" ? (
          <Field label="Paper content" hint="leave blank to use the seeded sample paper">
            <textarea
              rows={4}
              className={`${inputCls} resize-none font-mono text-xs`}
              placeholder="(using seeded sample paper)"
              value={form.paper_text}
              onChange={set("paper_text")}
            />
          </Field>
        ) : (
          <Field
            label="Blueprint"
            hint={`${
              bank?.length ?? 0
            } encrypted questions in the "${form.subject}" bank · sections + counts only`}
          >
            <textarea
              rows={7}
              className={`${inputCls} resize-none font-mono text-[11px] leading-relaxed`}
              value={blueprintText}
              onChange={(e) => setBlueprintText(e.target.value)}
            />
          </Field>
        )}

        <div className="flex items-center justify-between gap-3">
          <span className="flex items-center gap-1.5 text-xs text-faint">
            <Icon name="key" size={13} className="text-accent" />
            {mode === "dynamic"
              ? "per-candidate paper assembled at release · selection gated by the exam key"
              : "AES-256-GCM · split 3-of-5 · escrowed to cust1…cust5"}
          </span>
          <Button tone="solid" type="submit" loading={create.isPending} icon="lock">
            Seal &amp; Distribute
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

function BlueprintStrip({ examId }) {
  const { data: bp } = useBlueprint(examId);
  if (!bp || bp.assembly_mode !== "dynamic") return null;
  return (
    <div className="rounded-xl border border-royal/30 bg-royal/5 p-3">
      <div className="flex items-center gap-2">
        <Icon name="layers" size={14} className="text-royal" />
        <SectionLabel>dynamic assembly</SectionLabel>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-3">
        <MonoReadout label="bank pool" value={`${bp.pool_size} questions`} tone="accent" />
        <MonoReadout label="per candidate" value={`${bp.questions_per_paper} selected`} />
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-faint">
        Each candidate's paper is assembled at release from the encrypted bank; the
        selection is seeded by the exam key, so no one can predict it beforehand.
      </p>
    </div>
  );
}

function OpsPanel({ examId }) {
  const { data: status } = useUnlockStatus(examId, { poll: true });
  const { data: exams } = useExams();
  const exam = useMemo(() => exams?.find((e) => e.id === examId), [exams, examId]);

  if (!status || !exam) {
    return (
      <Card title="Live Operations" icon="activity">
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
      icon="activity"
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

        <div className="grid grid-cols-3 gap-3">
          <Metric
            label="quorum"
            value={`${status.shares_submitted}/${status.threshold_k}`}
            sub={`of ${status.num_custodians_n} custodians`}
            tone="accent"
            icon="users"
          />
          <Metric
            label="encryption"
            value="GCM"
            sub="AES-256"
            tone="verify"
            icon="shieldCheck"
          />
          <Metric
            label="status"
            value={status.time_locked ? "LOCKED" : "OPEN"}
            sub="time gate"
            tone={status.time_locked ? "danger" : "verify"}
            icon="clock"
          />
        </div>

        {exam.assembly_mode === "dynamic" && <BlueprintStrip examId={examId} />}

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
            <StatusPill tone="secure">AES-256-GCM</StatusPill>
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
    <Card title="Exams" subtitle={`${exams?.length || 0} sealed`} icon="database">
      <div className="flex flex-col gap-1.5">
        {(exams || []).map((e) => (
          <button
            key={e.id}
            onClick={() => onSelect(e.id)}
            className={`flex items-center justify-between rounded-xl border px-3 py-2.5 text-left transition-colors ${
              e.id === examId
                ? "border-accent/40 bg-accent/5"
                : "border-line hover:border-faint hover:bg-white/[0.015]"
            }`}
          >
            <div className="flex items-center gap-3">
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-lg border ${
                  e.status === "UNLOCKED"
                    ? "border-accent/30 bg-accent/10 text-accent"
                    : "border-danger/30 bg-danger/10 text-danger"
                }`}
              >
                <Icon name={e.status === "UNLOCKED" ? "unlock" : "lock"} size={15} />
              </span>
              <div>
                <div className="text-sm font-medium text-ink">{e.name}</div>
                <div className="mono text-[11px] text-faint">
                  #{e.id} · {e.center_id}
                </div>
              </div>
            </div>
            <StatusPill tone={e.status === "UNLOCKED" ? "secure" : "denied"}>
              {e.status}
            </StatusPill>
          </button>
        ))}
        {(!exams || exams.length === 0) && (
          <p className="py-3 text-center text-xs text-faint">no exams sealed yet</p>
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
      <PageHeader
        icon="gauge"
        title="Control Room"
        subtitle="Seal exams, distribute key shares, and monitor the vault in real time."
        right={<StatusPill tone="secure">{exams?.length || 0} exams</StatusPill>}
      />
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
