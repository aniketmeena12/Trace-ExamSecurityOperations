import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button, Card, MonoReadout, StatusPill } from "../components/primitives";
import { PageHeader } from "../components/PageHeader";
import { Icon } from "../components/Icon";
import { CountdownTimer } from "../components/CountdownTimer";
import { useAuth } from "../auth/AuthContext";
import { useExams, usePaperImage, useUnlockStatus } from "../api/hooks";

function LockedScreen({ status }) {
  const awaitingCustodians = !status.time_locked && status.status !== "UNLOCKED";
  return (
    <Card
      tone={awaitingCustodians ? "pending" : "denied"}
      icon={awaitingCustodians ? "unlock" : "lock"}
      iconTone={awaitingCustodians ? "pending" : "denied"}
      title="Examination Sealed"
      subtitle={status.status}
    >
      <div className="flex flex-col items-center gap-6 py-8">
        <motion.div
          animate={{ opacity: [0.55, 1, 0.55] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className={`flex h-24 w-24 items-center justify-center rounded-2xl border ${
            awaitingCustodians
              ? "border-warn/40 bg-warn/5 text-warn"
              : "border-danger/40 bg-danger/5 text-danger"
          }`}
        >
          <Icon name={awaitingCustodians ? "unlock" : "lock"} size={44} strokeWidth={1.5} />
        </motion.div>

        {status.time_locked ? (
          <>
            <p className="max-w-sm text-center text-sm text-muted">
              Your paper is encrypted and time-locked. It will unseal at the
              scheduled release.
            </p>
            <CountdownTimer seconds={status.seconds_remaining} size="lg" />
            <span className="kicker">time until release</span>
          </>
        ) : (
          <>
            <p className="text-sm text-warn">
              Release window is open — awaiting custodian authorization.
            </p>
            <div className="mono text-3xl font-bold tabular text-warn">
              {status.shares_submitted} / {status.threshold_k}
            </div>
            <span className="kicker">required custodian shares submitted</span>
          </>
        )}
      </div>
    </Card>
  );
}

function PaperViewer({ examId }) {
  const { data: image, error, isLoading } = usePaperImage(examId, true);

  return (
    <Card
      tone="secure"
      icon="file"
      iconTone="secure"
      title="Your Examination Paper"
      subtitle="released · per-candidate invisible watermark embedded"
      right={<StatusPill tone="secure">live</StatusPill>}
    >
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-accent/20 bg-accent/[0.04] px-3 py-2.5">
          <Icon name="fingerprint" size={20} className="text-accent" />
          <MonoReadout
            label="watermark fingerprint"
            value={image?.fingerprint || "…"}
            tone="accent"
          />
          <div className="flex-1 text-[11px] text-faint">
            Every copy is uniquely fingerprinted. If this leaks, it traces back
            to you.
          </div>
        </div>

        <div className="relative overflow-hidden rounded-xl border border-line bg-base">
          {/* subtle ops scanline over the document */}
          <div className="pointer-events-none absolute inset-0 z-10 bg-gradient-to-b from-accent/5 via-transparent to-accent/5" />
          <div className="pointer-events-none absolute inset-x-0 top-0 z-10 h-16 animate-scan bg-gradient-to-b from-accent/10 to-transparent" />
          {isLoading && (
            <div className="flex h-72 items-center justify-center gap-2 text-sm text-faint">
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
              decrypting &amp; rendering…
            </div>
          )}
          {error && (
            <div className="flex h-72 items-center justify-center text-sm text-danger">
              {error.message}
            </div>
          )}
          {image?.url && (
            <motion.img
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              src={image.url}
              alt="watermarked exam paper"
              className="mx-auto block max-h-[70vh] w-auto"
            />
          )}
        </div>

        {image?.url && (
          <div className="flex items-center justify-between gap-3">
            <span className="text-[11px] text-faint">
              For the demo: download this copy, then trace it from the
              Investigator console.
            </span>
            <a href={image.url} download={`exam-${examId}-watermarked.png`}>
              <Button tone="ghost" icon="download">
                Download copy
              </Button>
            </a>
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
    </div>
  );
}

export function CandidateDashboard() {
  const { active } = useAuth();
  const { data: exams } = useExams();
  const [examId, setExamId] = useState(null);
  const { data: status } = useUnlockStatus(examId, { poll: true });

  useEffect(() => {
    if (examId == null && exams && exams.length) {
      setExamId(exams[exams.length - 1].id);
    }
  }, [exams, examId]);

  const unlocked = status?.status === "UNLOCKED";

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon="user"
        title="Candidate Portal"
        subtitle={
          <>
            {active?.me?.display_name} · roll{" "}
            <span className="mono text-accent">{active?.me?.candidate_code}</span> ·
            center <span className="mono text-accent">{active?.me?.center_id}</span>
          </>
        }
        right={
          <StatusPill tone={unlocked ? "secure" : "pending"}>
            {unlocked ? "paper available" : "sealed"}
          </StatusPill>
        }
      />

      <ExamPicker examId={examId} onSelect={setExamId} />

      {!status ? (
        <Card title="Candidate Portal" icon="user">
          <p className="text-sm text-faint">Select an exam.</p>
        </Card>
      ) : unlocked ? (
        <PaperViewer examId={examId} />
      ) : (
        <LockedScreen status={status} />
      )}
    </div>
  );
}
