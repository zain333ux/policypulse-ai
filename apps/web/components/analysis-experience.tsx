"use client";

import {
  AlertTriangle,
  ArrowLeft,
  Check,
  ChevronRight,
  Circle,
  Download,
  FileText,
  LoaderCircle,
  MessageSquareQuote,
  RefreshCw,
  Scale,
  X,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ConcernChart } from "@/components/concern-chart";
import { API_URL, exportReport, getAnalysis, presentApiError } from "@/lib/api";
import type {
  AnalysisJob,
  AnalysisResult,
  Concern,
  Gap,
  Recommendation,
  SourceItem,
} from "@/lib/types";

type SectionId = "overview" | "concerns" | "gaps" | "recommendations" | "memo";

const sections: { id: SectionId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "concerns", label: "Public concerns" },
  { id: "gaps", label: "Policy gaps" },
  { id: "recommendations", label: "Recommendations" },
  { id: "memo", label: "Executive memo" },
];

export function AnalysisExperience({ analysisId }: { analysisId: string }) {
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const next = await getAnalysis(analysisId);
      setJob(next);
      setError(next.error ? presentApiError(new Error(next.error)) : "");
      return next;
    } catch (caught) {
      setError(presentApiError(caught));
      return null;
    }
  }, [analysisId]);

  useEffect(() => {
    let active = true;
    let interval: ReturnType<typeof setInterval> | undefined;
    const events = new EventSource(`${API_URL}/v1/analyses/${analysisId}/events`);

    const sync = async () => {
      if (!active) return;
      const next = await refresh();
      if (next?.status === "completed" || next?.status === "failed") {
        events.close();
        if (interval) clearInterval(interval);
      }
    };

    events.onmessage = sync;
    events.onerror = () => {
      events.close();
      interval = setInterval(sync, 1_000);
    };
    void sync();
    return () => {
      active = false;
      events.close();
      if (interval) clearInterval(interval);
    };
  }, [analysisId, refresh]);

  if (error && job?.status === "failed") {
    return <AnalysisError message={error} onRetry={() => void refresh()} />;
  }
  if (!job || job.status !== "completed" || !job.result) {
    return <AnalysisProgress job={job} error={error} />;
  }
  return <ResultsWorkspace result={job.result} />;
}

function AnalysisProgress({ job, error }: { job: AnalysisJob | null; error: string }) {
  const stages = job?.stages ?? defaultStages;
  const completed = stages.filter((stage) => stage.status === "completed").length;
  const progressPercentage = Math.round((completed / stages.length) * 100);
  return (
    <main className="mx-auto min-h-[75dvh] max-w-4xl px-4 py-12 sm:px-6 sm:py-16">
      <Link
        href="/"
        className="mb-5 inline-flex min-h-11 items-center gap-2 rounded-xl text-sm font-semibold"
        style={{ color: "var(--muted-foreground)" }}
      >
        <ArrowLeft aria-hidden="true" size={18} />
        Back to workspace
      </Link>
      <section className="surface rounded-3xl p-5 sm:p-8">
        <div className="flex items-start gap-4">
          <span
            className="grid size-12 shrink-0 place-items-center rounded-2xl"
            style={{ background: "var(--primary-soft)", color: "var(--primary)" }}
          >
            <LoaderCircle className="animate-spin" aria-hidden="true" size={24} />
          </span>
          <div>
            <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
              Live analysis
            </p>
            <h1 className="mt-1 text-2xl font-semibold sm:text-3xl">
              Building an evidence-grounded consultation report
            </h1>
            <p className="mt-2" style={{ color: "var(--muted-foreground)" }}>
              Each stage is validated before its findings appear in the report.
            </p>
          </div>
        </div>

        <div className="mt-7" aria-label={`Analysis ${progressPercentage}% complete`}>
          <div className="mb-2 flex justify-between text-sm font-semibold">
            <span>Pipeline progress</span>
            <span>{progressPercentage}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-[var(--border)]">
            <div
              className="h-full rounded-full bg-[var(--primary)] transition-[width] duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        <ol className="mt-5 space-y-3" aria-live="polite">
          {stages.map((stage) => (
            <li
              key={stage.id}
              className="flex items-center gap-4 rounded-2xl border bg-[var(--surface-subtle)] p-4"
            >
              <StageIcon status={stage.status} />
              <div className="min-w-0 flex-1">
                <p className="font-semibold">{stage.label}</p>
                <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
                  {stage.message}
                </p>
              </div>
              <span
                className="text-sm font-semibold capitalize"
                style={{
                  color:
                    stage.status === "completed"
                      ? "var(--success)"
                      : stage.status === "failed"
                        ? "var(--danger)"
                        : "var(--faint-foreground)",
                }}
              >
                {stage.status}
              </span>
            </li>
          ))}
        </ol>
        {error && (
          <p className="mt-5 text-sm" role="alert" style={{ color: "var(--danger)" }}>
            {error}
          </p>
        )}
      </section>
    </main>
  );
}

const defaultStages = [
  { id: "prepare", label: "Prepare evidence", status: "queued" as const, message: "Connecting to analysis" },
  { id: "policy", label: "Extract policy", status: "queued" as const, message: "Waiting" },
  { id: "coding", label: "Code stakeholder comments", status: "queued" as const, message: "Waiting" },
  { id: "sentiment", label: "Calculate sentiment", status: "queued" as const, message: "Waiting" },
  { id: "concerns", label: "Synthesize concerns", status: "queued" as const, message: "Waiting" },
  { id: "gaps", label: "Detect policy gaps", status: "queued" as const, message: "Waiting" },
  { id: "recommendations", label: "Build recommendations", status: "queued" as const, message: "Waiting" },
  { id: "quality", label: "Validate final evidence", status: "queued" as const, message: "Waiting" },
];

function StageIcon({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <span className="grid size-9 place-items-center rounded-full bg-[var(--success-soft)] text-[var(--success)]">
        <Check aria-hidden="true" size={18} />
      </span>
    );
  }
  if (status === "running") {
    return (
      <span className="grid size-9 place-items-center rounded-full bg-[var(--primary-soft)] text-[var(--primary)]">
        <LoaderCircle className="animate-spin" aria-hidden="true" size={18} />
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="grid size-9 place-items-center rounded-full bg-[var(--danger-soft)] text-[var(--danger)]">
        <AlertTriangle aria-hidden="true" size={18} />
      </span>
    );
  }
  return (
    <span className="grid size-9 place-items-center rounded-full border text-[var(--faint-foreground)]">
      <Circle aria-hidden="true" size={13} />
    </span>
  );
}

function AnalysisError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <main className="mx-auto grid min-h-[70dvh] max-w-3xl place-items-center px-4 py-16">
      <section className="surface rounded-3xl p-8 text-center">
        <AlertTriangle className="mx-auto text-[var(--danger)]" aria-hidden="true" size={32} />
        <h1 className="mt-5 text-2xl font-semibold">The analysis stopped safely</h1>
        <p className="mt-3" style={{ color: "var(--muted-foreground)" }}>
          {message}
        </p>
        <p className="mt-2 text-sm" style={{ color: "var(--faint-foreground)" }}>
          This public deployment is intended for showcasing the product experience, so temporary provider limits can occasionally interrupt a live run. We are sorry when that happens — the AI agents are talented, but still not fully immune to demo-day drama 🙂
        </p>
        <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[var(--primary)] px-5 font-semibold text-[var(--on-primary)]"
          >
            <RefreshCw aria-hidden="true" size={18} />
            Check again
          </button>
          <Link
            href="/"
            className="inline-flex min-h-11 items-center justify-center rounded-xl border px-5 font-semibold"
          >
            Start another analysis
          </Link>
        </div>
      </section>
    </main>
  );
}

function ResultsWorkspace({ result }: { result: AnalysisResult }) {
  const [section, setSection] = useState<SectionId>("overview");
  const [selectedEvidence, setSelectedEvidence] = useState<{
    source: SourceItem;
    finding: string;
  } | null>(null);
  const [exporting, setExporting] = useState<"markdown" | "pdf" | null>(null);

  const sourceMap = useMemo(
    () => new Map(result.sources.map((source) => [source.id, source])),
    [result.sources],
  );

  function openEvidence(id: string, finding: string) {
    const source = sourceMap.get(id);
    if (source) setSelectedEvidence({ source, finding });
  }

  async function download(format: "markdown" | "pdf") {
    setExporting(format);
    try {
      const blob = await exportReport(result, format);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `policypulse-report.${format === "pdf" ? "pdf" : "md"}`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(null);
    }
  }

  return (
    <main className="mx-auto max-w-[1500px] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-4 border-b pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-4xl">
          <Link
            href="/"
            className="mb-4 inline-flex min-h-11 items-center gap-2 rounded-xl text-sm font-semibold"
            style={{ color: "var(--muted-foreground)" }}
          >
            <ArrowLeft aria-hidden="true" size={18} />
            New consultation
          </Link>
          <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
            Consultation report
          </p>
          <h1 className="mt-1 text-2xl font-semibold sm:text-4xl">{result.policy.title}</h1>
          <p className="mt-3 max-w-3xl" style={{ color: "var(--muted-foreground)" }}>
            {result.policy.summary}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <ExportButton
            label="Markdown"
            busy={exporting === "markdown"}
            onClick={() => void download("markdown")}
          />
          <ExportButton label="PDF report" busy={exporting === "pdf"} onClick={() => void download("pdf")} primary />
        </div>
      </div>

      <div className="mb-5 flex gap-2 overflow-x-auto pb-2 lg:hidden" aria-label="Report sections">
        {sections.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setSection(item.id)}
            className="min-h-11 shrink-0 rounded-xl border px-4 text-sm font-semibold"
            style={
              section === item.id
                ? { background: "var(--primary-soft)", color: "var(--primary-strong)", borderColor: "var(--primary)" }
                : undefined
            }
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[220px_minmax(0,1fr)] xl:grid-cols-[220px_minmax(0,1fr)_360px]">
        <aside className="surface sticky top-24 hidden h-fit rounded-2xl p-3 lg:block">
          <nav aria-label="Report sections" className="space-y-1">
            {sections.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSection(item.id)}
                className="flex min-h-11 w-full items-center justify-between rounded-xl px-3 text-left text-sm font-semibold transition-colors"
                style={
                  section === item.id
                    ? { background: "var(--primary-soft)", color: "var(--primary-strong)" }
                    : { color: "var(--muted-foreground)" }
                }
              >
                {item.label}
                <ChevronRight aria-hidden="true" size={16} />
              </button>
            ))}
          </nav>
          <div className="mt-3 border-t px-3 pt-4 text-sm" style={{ color: "var(--faint-foreground)" }}>
            Generated {new Date(result.generated_at).toLocaleString()}
          </div>
        </aside>

        <section className="min-w-0">
          {section === "overview" && <Overview result={result} openEvidence={openEvidence} />}
          {section === "concerns" && <Concerns concerns={result.concerns} openEvidence={openEvidence} />}
          {section === "gaps" && <Gaps gaps={result.gaps} openEvidence={openEvidence} />}
          {section === "recommendations" && (
            <Recommendations recommendations={result.recommendations} openEvidence={openEvidence} />
          )}
          {section === "memo" && <Memo result={result} />}
        </section>

        <div className="hidden xl:block">
          <EvidencePanel selected={selectedEvidence} onClose={() => setSelectedEvidence(null)} />
        </div>
      </div>

      {selectedEvidence && (
        <div className="fixed inset-0 z-50 xl:hidden" role="dialog" aria-modal="true" aria-label="Source evidence">
          <button
            type="button"
            className="absolute inset-0 bg-slate-950/60"
            aria-label="Close evidence"
            onClick={() => setSelectedEvidence(null)}
          />
          <div className="absolute inset-x-0 bottom-0 max-h-[82dvh] overflow-y-auto rounded-t-3xl bg-[var(--surface)] p-5 shadow-2xl">
            <EvidenceContent selected={selectedEvidence} onClose={() => setSelectedEvidence(null)} />
          </div>
        </div>
      )}
    </main>
  );
}

function Overview({
  result,
  openEvidence,
}: {
  result: AnalysisResult;
  openEvidence: (id: string, finding: string) => void;
}) {
  const critical = result.gaps.filter((gap) => gap.severity === "critical").length;
  const ingestionWarnings = formatProcessingNotes(result.ingestion_warnings ?? []);
  return (
    <div className="space-y-6">
      {ingestionWarnings.length > 0 && (
        <section className="rounded-2xl border bg-[var(--warning-soft)] p-5">
          <div className="flex items-center gap-2 text-[var(--warning)]">
            <AlertTriangle aria-hidden="true" size={19} />
            <h2 className="font-semibold">Processing notes</h2>
          </div>
          <ul className="mt-3 space-y-1 text-sm text-[var(--warning)]">
            {ingestionWarnings.map((warning) => (
              <li key={warning}>• {warning}</li>
            ))}
          </ul>
        </section>
      )}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Comments analyzed" value={String(result.sources.filter((item) => item.type === "comment").length)} />
        <Metric label="Top concerns" value={String(result.concerns.length)} />
        <Metric label="Critical gaps" value={String(critical)} tone={critical ? "danger" : "success"} />
        <Metric label="Overall mood" value={result.sentiment.overall_mood} compact />
      </div>

      <section className="surface rounded-2xl p-5 sm:p-6">
        <div className="flex items-center gap-3">
          <Scale aria-hidden="true" size={21} style={{ color: "var(--primary)" }} />
          <h2 className="text-xl font-semibold">Sentiment distribution</h2>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <SentimentCard label="Support" value={result.sentiment.support} tone="success" />
          <SentimentCard label="Opposition" value={result.sentiment.opposition} tone="danger" />
          <SentimentCard label="Neutral or mixed" value={result.sentiment.neutral} tone="neutral" />
        </div>
      </section>

      <section className="surface rounded-2xl p-5 sm:p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
              Highest-frequency themes
            </p>
            <h2 className="mt-1 text-xl font-semibold">What stakeholders raised most often</h2>
          </div>
          <MessageSquareQuote aria-hidden="true" size={23} style={{ color: "var(--primary)" }} />
        </div>
        <div className="mt-5">
          <ConcernChart concerns={result.concerns.slice(0, 5)} />
        </div>
        <div className="mt-5 space-y-3">
          {result.concerns.slice(0, 3).map((concern) => (
            <FindingSummary key={concern.id} title={concern.theme} text={concern.summary}>
              <EvidenceButtons ids={concern.evidence_ids} finding={concern.theme} onOpen={openEvidence} />
            </FindingSummary>
          ))}
        </div>
      </section>
    </div>
  );
}

function Concerns({
  concerns,
  openEvidence,
}: {
  concerns: Concern[];
  openEvidence: (id: string, finding: string) => void;
}) {
  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Public concerns"
        title="Themes grounded in stakeholder comments"
        description="Frequency describes this uploaded dataset, not the wider population."
      />
      <section className="surface rounded-2xl p-5 sm:p-6">
        <ConcernChart concerns={concerns} />
      </section>
      <div className="space-y-4">
        {[...concerns]
          .sort((a, b) => b.percentage - a.percentage)
          .map((concern) => (
            <article key={concern.id} className="surface rounded-2xl p-5 sm:p-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-xl font-semibold">{concern.theme}</h2>
                    <Badge tone={concern.urgency === "high" ? "danger" : concern.urgency === "medium" ? "warning" : "neutral"}>
                      {concern.urgency} urgency
                    </Badge>
                    {concern.limited_evidence && <Badge tone="warning">Limited evidence</Badge>}
                  </div>
                  <p className="mt-3" style={{ color: "var(--muted-foreground)" }}>
                    {concern.summary}
                  </p>
                </div>
                <div className="shrink-0 rounded-xl bg-[var(--primary-soft)] px-4 py-3 text-center">
                  <strong className="block text-xl text-[var(--primary-strong)]">{concern.percentage.toFixed(0)}%</strong>
                  <span className="text-sm text-[var(--muted-foreground)]">{concern.count} comments</span>
                </div>
              </div>
              <EvidenceButtons ids={concern.evidence_ids} finding={concern.theme} onOpen={openEvidence} />
            </article>
          ))}
      </div>
    </div>
  );
}

function Gaps({
  gaps,
  openEvidence,
}: {
  gaps: Gap[];
  openEvidence: (id: string, finding: string) => void;
}) {
  const order = { critical: 0, high: 1, medium: 2, low: 3 };
  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Policy gaps"
        title="Where the draft does not match stakeholder needs"
        description="Coverage is assessed against the supplied draft and evidence—not against external legal standards."
      />
      <div className="space-y-4">
        {[...gaps]
          .sort((a, b) => order[a.severity] - order[b.severity])
          .map((gap) => (
            <article key={gap.id} className="surface rounded-2xl p-5 sm:p-6">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={gap.severity === "critical" || gap.severity === "high" ? "danger" : "warning"}>
                  {gap.severity}
                </Badge>
                <Badge tone={gap.covered_in_policy ? "success" : "neutral"}>
                  {gap.covered_in_policy ? "Partially covered" : "Not covered"}
                </Badge>
                {gap.limited_evidence && <Badge tone="warning">Limited evidence</Badge>}
              </div>
              <h2 className="mt-4 text-xl font-semibold">{gap.title}</h2>
              <p className="mt-3" style={{ color: "var(--muted-foreground)" }}>
                {gap.description}
              </p>
              <div className="mt-5 rounded-2xl border bg-[var(--surface-subtle)] p-4">
                <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
                  Suggested fix
                </p>
                <p className="mt-1">{gap.suggested_fix}</p>
              </div>
              <EvidenceButtons ids={gap.evidence_ids} finding={gap.title} onOpen={openEvidence} />
            </article>
          ))}
      </div>
    </div>
  );
}

function Recommendations({
  recommendations,
  openEvidence,
}: {
  recommendations: Recommendation[];
  openEvidence: (id: string, finding: string) => void;
}) {
  const order = { critical: 0, important: 1, "nice-to-have": 2 };
  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Recommendations"
        title="Prioritized actions for the next policy revision"
        description="Treat these as a structured starting point for human policy review."
      />
      <div className="space-y-4">
        {[...recommendations]
          .sort((a, b) => order[a.priority] - order[b.priority])
          .map((recommendation) => (
            <article key={recommendation.id} className="surface rounded-2xl p-5 sm:p-6">
              <Badge tone={recommendation.priority === "critical" ? "danger" : recommendation.priority === "important" ? "warning" : "neutral"}>
                {recommendation.priority}
              </Badge>
              <h2 className="mt-4 text-xl font-semibold">{recommendation.title}</h2>
              <p className="mt-3 text-lg">{recommendation.action}</p>
              <p className="mt-3" style={{ color: "var(--muted-foreground)" }}>
                {recommendation.rationale}
              </p>
              {recommendation.revised_wording && (
                <blockquote className="mt-5 rounded-2xl border-l-4 border-l-[var(--primary)] bg-[var(--surface-subtle)] p-4">
                  <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
                    Suggested wording
                  </p>
                  <p className="mt-2">{recommendation.revised_wording}</p>
                </blockquote>
              )}
              <EvidenceButtons ids={recommendation.evidence_ids} finding={recommendation.title} onOpen={openEvidence} />
            </article>
          ))}
      </div>
    </div>
  );
}

function Memo({ result }: { result: AnalysisResult }) {
  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Executive memo"
        title="A concise brief for decision-makers"
        description="AI-generated content. Review, edit, and validate before formal use."
      />
      <article className="surface rounded-2xl p-6 sm:p-10">
        <div className="flex items-center justify-between gap-4 border-b pb-5">
          <div>
            <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
              POLICY CONSULTATION MEMO
            </p>
            <h2 className="mt-1 text-xl font-semibold">{result.policy.title}</h2>
          </div>
          <FileText aria-hidden="true" size={24} style={{ color: "var(--primary)" }} />
        </div>
        <div className="mt-7 space-y-5 text-[17px] leading-8">
          {result.executive_memo.split("\n\n").map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>
      </article>
      <section className="rounded-2xl border bg-[var(--surface-subtle)] p-5">
        <h2 className="font-semibold">Methodology and limitations</h2>
        <p className="mt-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
          {result.methodology}
        </p>
        <ul className="mt-4 space-y-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
          {result.limitations.map((limitation) => (
            <li key={limitation} className="flex gap-2">
              <AlertTriangle className="mt-0.5 shrink-0" aria-hidden="true" size={16} />
              {limitation}
            </li>
          ))}
        </ul>
      </section>
      <section className="rounded-2xl border bg-[var(--surface-subtle)] p-5">
        <h2 className="font-semibold">Showcase deployment note</h2>
        <p className="mt-2 text-sm leading-6" style={{ color: "var(--muted-foreground)" }}>
          This public deployment is provided to demonstrate the PolicyPulse AI workflow and reporting experience.
          Because the app depends on live third-party AI providers, analyses may occasionally be delayed, rate-limited,
          or temporarily unavailable during periods of higher usage. If that happens, please retry shortly or use the
          verified sample scenario included in the workspace.
        </p>
      </section>
    </div>
  );
}

function formatProcessingNotes(warnings: string[]): string[] {
  return warnings.map((warning) => {
    const normalized = warning.toLowerCase();
    if (normalized.includes("policy text was analyzed in multiple passes")) {
      return "Large submission analyzed in multiple passes so the full policy could be reviewed within live model limits.";
    }
    if (normalized.includes("comment evidence was analyzed in multiple passes")) {
      return "Large comment set analyzed in multiple passes so broader stakeholder feedback could still be included.";
    }
    if (normalized.includes("gap detection used compact evidence excerpts")) {
      return "Some evidence excerpts were shortened during gap detection to keep the live analysis stable.";
    }
    if (normalized.includes("condensed")) {
      return "Parts of the uploaded material were condensed to fit the live analysis window while preserving the main evidence trail.";
    }
    return warning;
  });
}

function EvidencePanel({
  selected,
  onClose,
}: {
  selected: { source: SourceItem; finding: string } | null;
  onClose: () => void;
}) {
  return (
    <aside className="surface sticky top-24 min-h-72 rounded-2xl p-5" aria-label="Source evidence">
      {selected ? (
        <EvidenceContent selected={selected} onClose={onClose} />
      ) : (
        <div className="grid min-h-64 place-items-center text-center">
          <div>
            <MessageSquareQuote className="mx-auto" aria-hidden="true" size={27} style={{ color: "var(--primary)" }} />
            <h2 className="mt-4 font-semibold">Inspect the evidence</h2>
            <p className="mt-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
              Select any evidence badge to view the exact source passage or comment.
            </p>
          </div>
        </div>
      )}
    </aside>
  );
}

function EvidenceContent({
  selected,
  onClose,
}: {
  selected: { source: SourceItem; finding: string };
  onClose: () => void;
}) {
  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold capitalize" style={{ color: "var(--primary)" }}>
            {selected.source.type} evidence · {selected.source.id}
          </p>
          <h2 className="mt-1 text-lg font-semibold">Source detail</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="grid size-11 place-items-center rounded-xl border hover:bg-[var(--surface-subtle)]"
          aria-label="Close evidence"
        >
          <X aria-hidden="true" size={19} />
        </button>
      </div>
      <blockquote className="mt-5 rounded-2xl border-l-4 border-l-[var(--primary)] bg-[var(--surface-subtle)] p-4 text-[17px] leading-7">
        “{selected.source.text}”
      </blockquote>
      <div className="mt-5 border-t pt-4">
        <p className="text-sm font-semibold">Related finding</p>
        <p className="mt-1 text-sm" style={{ color: "var(--muted-foreground)" }}>
          {selected.finding}
        </p>
      </div>
    </>
  );
}

function EvidenceButtons({
  ids,
  finding,
  onOpen,
}: {
  ids: string[];
  finding: string;
  onOpen: (id: string, finding: string) => void;
}) {
  if (!ids.length) return <Badge tone="warning">Limited evidence</Badge>;
  return (
    <div className="mt-5 flex flex-wrap gap-2" aria-label={`Evidence for ${finding}`}>
      {ids.map((id) => (
        <button
          key={id}
          type="button"
          onClick={() => onOpen(id, finding)}
          className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border px-3 text-sm font-semibold transition-colors hover:border-[var(--primary)] hover:bg-[var(--primary-soft)]"
        >
          <MessageSquareQuote aria-hidden="true" size={15} />
          {id}
        </button>
      ))}
    </div>
  );
}

function ExportButton({
  label,
  busy,
  onClick,
  primary = false,
}: {
  label: string;
  busy: boolean;
  onClick: () => void;
  primary?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={busy}
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border px-4 font-semibold transition disabled:opacity-60 ${
        primary ? "bg-[var(--primary)] text-[var(--on-primary)] hover:bg-[var(--primary-strong)]" : "hover:bg-[var(--surface-subtle)]"
      }`}
    >
      {busy ? <LoaderCircle className="animate-spin" aria-hidden="true" size={18} /> : <Download aria-hidden="true" size={18} />}
      {label}
    </button>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <header>
      <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
        {eyebrow}
      </p>
      <h2 className="mt-1 text-2xl font-semibold sm:text-3xl">{title}</h2>
      <p className="mt-2" style={{ color: "var(--muted-foreground)" }}>
        {description}
      </p>
    </header>
  );
}

function Metric({
  label,
  value,
  tone = "primary",
  compact = false,
}: {
  label: string;
  value: string;
  tone?: "primary" | "danger" | "success";
  compact?: boolean;
}) {
  const color = tone === "danger" ? "var(--danger)" : tone === "success" ? "var(--success)" : "var(--primary)";
  return (
    <article className="surface rounded-2xl p-5">
      <p className="text-sm font-semibold" style={{ color: "var(--muted-foreground)" }}>
        {label}
      </p>
      <p className={`mt-2 font-[family-name:var(--font-lexend)] font-semibold ${compact ? "text-lg" : "text-3xl"}`} style={{ color }}>
        {value}
      </p>
    </article>
  );
}

function SentimentCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "danger" | "neutral";
}) {
  const color = tone === "success" ? "var(--success)" : tone === "danger" ? "var(--danger)" : "var(--muted-foreground)";
  return (
    <div className="rounded-2xl border bg-[var(--surface-subtle)] p-4">
      <p className="text-sm font-semibold" style={{ color: "var(--muted-foreground)" }}>
        {label}
      </p>
      <p className="mt-1 text-3xl font-semibold" style={{ color }}>
        {value}%
      </p>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-[var(--border)]">
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  );
}

function FindingSummary({
  title,
  text,
  children,
}: {
  title: string;
  text: string;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-2xl border bg-[var(--surface-subtle)] p-4">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-1 text-sm" style={{ color: "var(--muted-foreground)" }}>
        {text}
      </p>
      {children}
    </article>
  );
}

function Badge({
  tone,
  children,
}: {
  tone: "danger" | "warning" | "success" | "neutral";
  children: React.ReactNode;
}) {
  const colors = {
    danger: { background: "var(--danger-soft)", color: "var(--danger)" },
    warning: { background: "var(--warning-soft)", color: "var(--warning)" },
    success: { background: "var(--success-soft)", color: "var(--success)" },
    neutral: { background: "var(--surface-subtle)", color: "var(--muted-foreground)" },
  };
  return (
    <span className="inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold capitalize" style={colors[tone]}>
      {children}
    </span>
  );
}
