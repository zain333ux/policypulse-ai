"use client";

import {
  ArrowRight,
  Check,
  FileText,
  LoaderCircle,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  ClipboardList,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { createAnalysis, parseInputs } from "@/lib/api";

const DEMO_POLICY = `University Attendance and Academic Participation Policy

Students must maintain at least 85% attendance in every enrolled course. A student whose attendance falls below 85% will not be permitted to sit the final examination for that course.

Faculty members are responsible for recording attendance and reporting shortages before final examinations. The policy takes effect at the beginning of the next academic term.

The university may review exceptional cases at its discretion.`;

const DEMO_COMMENTS = [
  "Attendance matters, but an automatic exam ban is too harsh without an appeal.",
  "Working students need limited flexibility when shifts cannot be changed.",
  "There must be a documented medical exemption for hospitalization and chronic illness.",
  "Students with disabilities need reasonable accommodations.",
  "Public transport delays make an inflexible threshold unfair for commuters.",
  "I support stronger attendance because students learn more when they attend class.",
  "Who corrects the record when a lecturer marks a student absent by mistake?",
  "The university should warn students early and provide an appeal deadline.",
  "Medical documents should be reviewed consistently across departments.",
  "The rule is useful, but exceptions and dispute handling must be clearly written.",
].join("\n");

export function InputWorkspace() {
  const router = useRouter();
  const [policyText, setPolicyText] = useState("");
  const [commentsText, setCommentsText] = useState("");
  const [policyFile, setPolicyFile] = useState<File | null>(null);
  const [commentsFile, setCommentsFile] = useState<File | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const comments = useMemo(
    () => commentsText.split("\n").map((item) => item.trim()).filter(Boolean),
    [commentsText],
  );

  function loadDemo() {
    setPolicyText(DEMO_POLICY);
    setCommentsText(DEMO_COMMENTS);
    setPolicyFile(null);
    setCommentsFile(null);
    setIsDemo(true);
    setError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.set("policy_text", policyText);
      formData.set("comments_text", commentsText);
      if (policyFile) formData.set("policy_file", policyFile);
      if (commentsFile) formData.set("comments_file", commentsFile);
      const parsed = await parseInputs(formData);
      const created = await createAnalysis({
        policy_text: parsed.policy_text,
        comments: parsed.comments,
        demo: isDemo,
        ingestion_warnings: parsed.warnings,
      });
      router.push(`/analysis/${created.id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The analysis could not be started.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="surface rounded-3xl p-4 sm:p-6 lg:p-8">
      <div className="mb-7 flex flex-col gap-4 border-b pb-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="mb-1 text-sm font-semibold" style={{ color: "var(--primary)" }}>
            Consultation workspace
          </p>
          <h2 className="text-2xl font-semibold">Add the policy and public feedback</h2>
        </div>
        <button
          type="button"
          onClick={loadDemo}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border px-4 font-semibold transition-colors hover:bg-[var(--surface-subtle)]"
        >
          <Sparkles aria-hidden="true" size={18} />
          Load verified sample
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <InputPanel
          step="01"
          title="Policy document"
          description="Upload PDF, DOCX, or TXT—or paste the draft directly."
          icon={<FileText aria-hidden="true" size={21} />}
          accept=".pdf,.docx,.txt"
          file={policyFile}
          onFile={(file) => {
            setPolicyFile(file);
            setIsDemo(false);
          }}
        >
          <label htmlFor="policy-text" className="mb-2 block font-semibold">
            Policy text
          </label>
          <textarea
            id="policy-text"
            value={policyText}
            onChange={(event) => {
              setPolicyText(event.target.value);
              setIsDemo(false);
            }}
            rows={12}
            className="min-h-72 w-full resize-y rounded-2xl border bg-[var(--surface)] px-4 py-3 text-base outline-none transition focus:border-[var(--focus)]"
            placeholder="Paste the proposed policy here…"
          />
          <p className="mt-2 text-sm" style={{ color: "var(--faint-foreground)" }}>
            {policyText.length.toLocaleString()} / 50,000 characters
          </p>
        </InputPanel>

        <InputPanel
          step="02"
          title="Public feedback"
          description="Upload CSV or TXT—or paste one comment per line."
          icon={<MessageSquareText aria-hidden="true" size={21} />}
          accept=".csv,.xlsx,.xls,.txt,.md"
          file={commentsFile}
          onFile={(file) => {
            setCommentsFile(file);
            setIsDemo(false);
          }}
        >
          <label htmlFor="comments-text" className="mb-2 block font-semibold">
            Comments
          </label>
          <textarea
            id="comments-text"
            value={commentsText}
            onChange={(event) => {
              setCommentsText(event.target.value);
              setIsDemo(false);
            }}
            rows={12}
            className="min-h-72 w-full resize-y rounded-2xl border bg-[var(--surface)] px-4 py-3 text-base outline-none transition focus:border-[var(--focus)]"
            placeholder={"Add one comment per line…\nMedical exemptions need clearer rules."}
          />
          <div
            className="mt-2 flex items-center justify-between text-sm"
            style={{ color: "var(--faint-foreground)" }}
          >
            <span>{comments.length} comments detected</span>
            <span>Maximum 500</span>
          </div>
        </InputPanel>
      </div>

      {error && (
        <div
          role="alert"
          className="mt-6 rounded-2xl border px-4 py-3"
          style={{ borderColor: "var(--danger)", background: "var(--danger-soft)", color: "var(--danger)" }}
        >
          <strong>Check your inputs.</strong> {error}
        </div>
      )}

      <div className="mt-7 flex flex-col gap-5 border-t pt-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex max-w-2xl items-start gap-3">
          <ShieldCheck className="mt-0.5 shrink-0" aria-hidden="true" size={20} style={{ color: "var(--primary)" }} />
          <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
            Files are parsed for this analysis and are not permanently stored. Content is sent to the
            configured AI provider. Avoid uploading confidential or personally identifying information.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/survey"
            className="inline-flex min-h-13 items-center justify-center gap-2 rounded-xl border px-5 font-semibold transition-colors hover:bg-[var(--surface-subtle)]"
          >
            <ClipboardList aria-hidden="true" size={19} />
            No feedback yet? Create survey
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex min-h-13 min-w-52 items-center justify-center gap-2 rounded-xl bg-[var(--primary)] px-6 font-semibold text-[var(--on-primary)] transition hover:bg-[var(--primary-strong)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <>
                <LoaderCircle className="animate-spin" aria-hidden="true" size={19} />
                Preparing analysis
              </>
            ) : (
              <>
                Analyze policy
                <ArrowRight aria-hidden="true" size={19} />
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}

function InputPanel({
  step,
  title,
  description,
  icon,
  accept,
  file,
  onFile,
  children,
}: {
  step: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  accept: string;
  file: File | null;
  onFile: (file: File | null) => void;
  children: React.ReactNode;
}) {
  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    onFile(event.target.files?.[0] ?? null);
  }

  return (
    <section className="rounded-2xl border bg-[var(--surface-subtle)] p-4 sm:p-5">
      <div className="mb-5 flex items-start gap-3">
        <span
          className="grid size-10 shrink-0 place-items-center rounded-xl border"
          style={{ background: "var(--surface)", color: "var(--primary)" }}
        >
          {icon}
        </span>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
              {step}
            </span>
            <h3 className="text-lg font-semibold">{title}</h3>
          </div>
          <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
            {description}
          </p>
        </div>
      </div>

      <label className="mb-5 flex min-h-24 items-center justify-center gap-3 rounded-2xl border border-dashed bg-[var(--surface)] px-4 text-center transition hover:border-[var(--primary)] hover:bg-[var(--primary-soft)]">
        <input type="file" accept={accept} onChange={handleFile} className="sr-only" />
        {file ? <Check aria-hidden="true" size={20} /> : <UploadCloud aria-hidden="true" size={21} />}
        <span>
          <span className="block font-semibold">{file ? file.name : "Choose a file"}</span>
          <span className="block text-sm" style={{ color: "var(--muted-foreground)" }}>
            {file ? `${Math.ceil(file.size / 1024)} KB selected` : "Up to 5 MB"}
          </span>
        </span>
      </label>
      {children}
    </section>
  );
}
