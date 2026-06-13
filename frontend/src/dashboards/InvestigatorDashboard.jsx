import { useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Button,
  Card,
  MonoReadout,
  SectionLabel,
  StatusPill,
  inputCls,
} from "../components/primitives";
import { PageHeader } from "../components/PageHeader";
import { Icon } from "../components/Icon";
import { LogView } from "../components/LogView";
import {
  useAudit,
  useCase,
  useCases,
  useLeakMatch,
  useTrace,
  useVerifyChain,
} from "../api/hooks";

function TraceResult({ result }) {
  if (!result) return null;
  if (!result.watermark_present) {
    return (
      <div className="rounded-xl border border-warn/30 bg-warn/5 p-4">
        <StatusPill tone="pending">no watermark detected</StatusPill>
        <p className="mt-2 text-sm text-muted">
          This image carries no recoverable Trace fingerprint
          <span className="mono text-faint"> (magic dist {result.magic_hd})</span>.
        </p>
      </div>
    );
  }
  const m = result.match;
  const conf = Math.round(result.confidence * 100);
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-danger/40 bg-danger/5 p-4 shadow-glow-danger"
    >
      <div className="flex items-center justify-between">
        <StatusPill tone="denied" pulse>
          leak source identified
        </StatusPill>
        <span className="mono text-xs text-faint">
          {result.bit_distance}/64 bit errors
        </span>
      </div>

      <div className="mt-4 flex items-baseline gap-3">
        <span className="kicker">traced to</span>
        <span className="mono text-2xl font-bold text-danger">
          {m ? m.candidate_id : "—"}
        </span>
        {m && (
          <span className="mono text-sm text-muted">
            center {m.center_id} · exam #{m.exam_id}
          </span>
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <MonoReadout
          label="recovered fingerprint"
          value={result.extracted_fingerprint}
          tone="danger"
        />
        <div className="flex flex-col gap-1">
          <span className="kicker">match confidence</span>
          <div className="flex items-center gap-2">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-line">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${conf}%` }}
                className="h-full bg-danger"
              />
            </div>
            <span className="mono text-sm text-danger">{conf}%</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function TracePanel() {
  const trace = useTrace();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const pick = (f) => {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    trace.reset();
  };

  return (
    <Card
      title="Forensic Trace"
      subtitle="upload a leaked image · recover its fingerprint"
      icon="crosshair"
      iconTone={trace.data?.watermark_present ? "denied" : "royal"}
      tone={trace.data?.watermark_present ? "denied" : undefined}
    >
      <div className="flex flex-col gap-4">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            pick(e.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
          className={`relative flex cursor-pointer flex-col items-center justify-center gap-3 overflow-hidden rounded-xl border border-dashed px-4 py-9 text-center transition-colors ${
            dragging ? "border-accent bg-accent/5" : "border-line hover:border-faint"
          }`}
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-royal/30 bg-royal/10 text-royal">
            <Icon name="upload" size={22} />
          </span>
          <span className="text-sm text-muted">
            Drop a leaked image here, or click to browse
          </span>
          <span className="text-[11px] text-faint">PNG / JPEG</span>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => pick(e.target.files?.[0])}
          />
        </div>

        {preview && (
          <div className="flex items-center gap-3 rounded-xl border border-line bg-base/40 p-3">
            <img
              src={preview}
              alt="evidence"
              className="h-16 w-16 rounded-md border border-line object-cover"
            />
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm text-ink">{file?.name}</div>
              <div className="mono text-[11px] text-faint">
                {(file?.size / 1024).toFixed(1)} KB
              </div>
            </div>
            <Button
              tone="danger"
              loading={trace.isPending}
              icon="scan"
              onClick={() => trace.mutate(file)}
            >
              Run Trace
            </Button>
          </div>
        )}

        {trace.isError && (
          <p className="text-xs text-danger">{trace.error.message}</p>
        )}
        <TraceResult result={trace.data} />
      </div>
    </Card>
  );
}

function LeakMatchResult({ result }) {
  if (!result) return null;
  if (!result.matched_questions.length) {
    return (
      <div className="rounded-xl border border-warn/30 bg-warn/5 p-4">
        <StatusPill tone="pending">no bank question matched</StatusPill>
        <p className="mt-2 text-sm text-muted">{result.note}</p>
      </div>
    );
  }
  const prime = result.suspects.filter((s) => s.has_all);
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-4 rounded-xl border border-danger/40 bg-danger/5 p-4 shadow-glow-danger"
    >
      <div className="flex items-center justify-between">
        <StatusPill tone="denied" pulse>
          {result.matched_questions.length} question(s) matched
        </StatusPill>
        <span className="mono text-xs text-faint">{result.leaked_chars} chars analysed</span>
      </div>
      <p className="text-sm text-ink">{result.note}</p>

      <div>
        <SectionLabel>matched questions</SectionLabel>
        <div className="flex flex-col gap-1.5">
          {result.matched_questions.map((q) => (
            <div
              key={q.question_id}
              className="flex items-center justify-between gap-3 rounded-lg border border-line bg-base/40 px-3 py-2"
            >
              <span className="min-w-0 flex-1 truncate text-sm text-muted">
                <span className="mono text-faint">#{q.question_id}</span> {q.prompt_preview}
              </span>
              <span className="mono text-xs text-danger">
                {Math.round(q.containment * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <SectionLabel>
          {prime.length ? "prime suspects (received every leaked question)" : "candidates with overlap"}
        </SectionLabel>
        <div className="flex flex-col gap-1.5">
          {(prime.length ? prime : result.suspects).slice(0, 8).map((s) => (
            <div
              key={`${s.exam_id}:${s.username}`}
              className="flex items-center justify-between gap-3 rounded-lg border border-danger/20 bg-danger/[0.04] px-3 py-2"
            >
              <span className="mono text-sm font-semibold text-danger">{s.candidate_code}</span>
              <span className="mono text-[11px] text-muted">
                {s.username} · exam #{s.exam_id} · {s.matched_of_leak} hit(s)
                {s.fingerprint ? ` · fp ${s.fingerprint}` : ""}
              </span>
            </div>
          ))}
          {!result.suspects.length && (
            <p className="text-xs text-faint">no issued paper contained these questions yet.</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function LeakMatchPanel() {
  const match = useLeakMatch();
  const [text, setText] = useState("");
  return (
    <Card
      title="Leak-Match Detector"
      subtitle="paste suspected leaked text · match to bank · narrow the source"
      icon="scan"
      iconTone={match.data?.matched_questions?.length ? "denied" : "royal"}
      tone={match.data?.matched_questions?.length ? "denied" : undefined}
    >
      <div className="flex flex-col gap-3">
        <textarea
          rows={4}
          className={`${inputCls} resize-none font-mono text-xs`}
          placeholder="Paste a question or whole paper circulating on chat / social…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="flex items-center justify-between gap-3">
          <span className="flex items-center gap-1.5 text-[11px] text-faint">
            <Icon name="layers" size={13} className="text-royal" />
            matches against the encrypted bank · intersects per-candidate selections
          </span>
          <Button
            tone="danger"
            icon="crosshair"
            loading={match.isPending}
            onClick={() => text.trim() && match.mutate(text)}
          >
            Match Leak
          </Button>
        </div>
        {match.isError && <p className="text-xs text-danger">{match.error.message}</p>}
        <LeakMatchResult result={match.data} />
      </div>
    </Card>
  );
}

function CandidateCard({ c }) {
  const rows = [
    ["roll number", c.candidate_code],
    ["name", c.display_name],
    ["exam centre", c.center_id],
    ["login", c.username],
    ["exam", c.exam_id != null ? `#${c.exam_id}` : null],
    ["watermark fingerprint", c.fingerprint],
    ["issued at", c.issued_at ? c.issued_at.slice(0, 19).replace("T", " ") : null],
    ["questions on paper", c.question_ids ? c.question_ids.join(", ") : null],
    ["match confidence", c.confidence != null ? `${Math.round(c.confidence * 100)}%` : null],
    ["matched of leak", c.matched_of_leak != null ? `${c.matched_of_leak}${c.has_all ? " (all)" : ""}` : null],
  ].filter(([, v]) => v != null && v !== "");
  return (
    <div className="rounded-xl border border-danger/30 bg-danger/[0.04] p-4">
      <div className="flex items-baseline justify-between">
        <span className="mono text-xl font-bold text-danger">{c.candidate_code || c.username}</span>
        {c.has_all && <StatusPill tone="denied">received all</StatusPill>}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2">
        {rows.map(([k, v]) => (
          <div key={k} className="flex flex-col">
            <span className="kicker">{k}</span>
            <span className="mono text-xs text-ink break-all">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function CaseDetail({ caseId }) {
  const { data: c } = useCase(caseId);
  if (!c) return <p className="text-xs text-faint">loading case…</p>;
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <StatusPill tone={c.kind === "image" ? "denied" : "royal"}>{c.kind} case #{c.id}</StatusPill>
        <span className="mono text-[11px] text-faint">
          {c.created_at.slice(0, 19).replace("T", " ")} · by {c.created_by}
        </span>
      </div>
      <p className="text-sm text-ink">{c.summary}</p>
      {c.suspects?.length ? (
        <div className="flex flex-col gap-2">
          <SectionLabel>implicated candidate{c.suspects.length > 1 ? "s" : ""} — full details</SectionLabel>
          {c.suspects.map((s) => (
            <CandidateCard key={`${s.exam_id}:${s.username}`} c={s} />
          ))}
        </div>
      ) : (
        <p className="text-xs text-faint">No candidate implicated in this case.</p>
      )}
    </div>
  );
}

function CaseFilesPanel() {
  const { data: cases } = useCases();
  const [openId, setOpenId] = useState(null);
  return (
    <Card
      title="Case Files"
      subtitle="every detection, with the full candidate profile — reopen any time"
      icon="database"
      iconTone="royal"
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="flex max-h-[420px] flex-col gap-1.5 overflow-auto pr-1">
          {(cases || []).map((k) => (
            <button
              key={k.id}
              onClick={() => setOpenId(k.id)}
              className={`flex flex-col rounded-lg border px-3 py-2 text-left transition-colors ${
                k.id === openId
                  ? "border-danger/40 bg-danger/5"
                  : "border-line hover:border-faint hover:bg-white/[0.015]"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="mono text-xs text-danger">
                  #{k.id} · {k.top_candidate || "no source"}
                </span>
                <span className="kicker">{k.kind}</span>
              </div>
              <span className="mt-0.5 truncate text-[11px] text-faint">{k.summary}</span>
            </button>
          ))}
          {!cases?.length && (
            <p className="py-3 text-center text-xs text-faint">
              no cases yet — run a trace or a leak match
            </p>
          )}
        </div>
        <div className="rounded-xl border border-line bg-base/30 p-3">
          {openId ? (
            <CaseDetail caseId={openId} />
          ) : (
            <p className="grid h-full place-items-center text-xs text-faint">
              select a case to see the candidate's full details
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}

function AuditLedger() {
  const { data: events } = useAudit();
  const verify = useVerifyChain();
  const result = verify.data;

  const tone = result ? (result.ok ? "verified" : "denied") : undefined;

  return (
    <Card
      title="Audit Ledger"
      subtitle="append-only SHA-256 hash chain"
      icon="hash"
      iconTone={tone || "idle"}
      tone={tone}
      right={
        <Button
          tone={result && !result.ok ? "danger" : "verify"}
          loading={verify.isPending}
          icon="shieldCheck"
          onClick={() => verify.mutate()}
        >
          Verify Integrity
        </Button>
      }
    >
      <div className="flex flex-col gap-3">
        {result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`flex items-center justify-between rounded-xl border px-3 py-2 ${
              result.ok
                ? "border-verify/30 bg-verify/5"
                : "border-danger/40 bg-danger/5"
            }`}
          >
            <StatusPill tone={result.ok ? "verified" : "denied"} pulse={!result.ok}>
              {result.ok ? "chain intact" : "chain broken"}
            </StatusPill>
            <span className="mono text-xs text-muted">
              {result.ok
                ? `${result.count} events verified`
                : `break at event #${result.first_broken}`}
            </span>
          </motion.div>
        )}

        <SectionLabel>event stream</SectionLabel>
        <LogView
          events={[...(events || [])].reverse()}
          brokenIds={result?.broken || []}
        />
      </div>
    </Card>
  );
}

export function InvestigatorDashboard() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon="crosshair"
        iconTone="royal"
        title="Forensics Console"
        subtitle="Trace leaked papers to their source and verify the tamper-evident audit chain."
      />
      <LeakMatchPanel />
      <CaseFilesPanel />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <TracePanel />
        <AuditLedger />
      </div>
    </div>
  );
}
