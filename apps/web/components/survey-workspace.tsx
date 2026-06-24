"use client";

import {
  ArrowLeft,
  Check,
  ClipboardList,
  Download,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  LoaderCircle,
  Send,
  UploadCloud,
} from "lucide-react";
import Link from "next/link";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import {
  createGoogleForm,
  exportSurveyTemplate,
  generateSurvey,
  parsePolicy,
} from "@/lib/api";
import type { GoogleFormDeployment, SurveyBlueprint } from "@/lib/types";

const SURVEY_DEMO_POLICY = `University Attendance and Academic Participation Policy

Students must maintain at least 85% attendance in every enrolled course. Students below the
threshold cannot sit final examinations. Faculty members record attendance weekly. Exceptional
cases may be reviewed by the department chair, but the policy does not define eligibility,
medical exemptions, disability accommodations, or an appeal process.`;

export function SurveyWorkspace() {
  const [policyText, setPolicyText] = useState("");
  const [policyFile, setPolicyFile] = useState<File | null>(null);
  const [blueprint, setBlueprint] = useState<SurveyBlueprint | null>(null);
  const [deployment, setDeployment] = useState<GoogleFormDeployment | null>(null);
  const [loading, setLoading] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [progressIndex, setProgressIndex] = useState(0);
  const [error, setError] = useState("");

  const progress = [
    "Extracting policy rules and affected groups",
    "Designing neutral consultation questions",
    "Validating question balance and response types",
  ];

  useEffect(() => {
    if (!loading) return;
    const timer = window.setInterval(
      () => setProgressIndex((current) => Math.min(current + 1, progress.length - 1)),
      900,
    );
    return () => window.clearInterval(timer);
  }, [loading, progress.length]);

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setProgressIndex(0);
    setError("");
    setDeployment(null);
    try {
      const form = new FormData();
      form.set("policy_text", policyText);
      if (policyFile) form.set("policy_file", policyFile);
      const parsed = await parsePolicy(form);
      const generated = await generateSurvey(parsed.policy_text);
      setBlueprint(generated);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The survey could not be generated.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDeploy() {
    if (!blueprint) return;
    setDeploying(true);
    setError("");
    try {
      setDeployment(await createGoogleForm(blueprint));
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The Google Form could not be created.",
      );
    } finally {
      setDeploying(false);
    }
  }

  async function downloadTemplate() {
    if (!blueprint) return;
    const blob = await exportSurveyTemplate(blueprint);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "policy-survey-responses.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <Link
        href="/"
        className="inline-flex min-h-11 items-center gap-2 rounded-xl text-sm font-semibold"
        style={{ color: "var(--muted-foreground)" }}
      >
        <ArrowLeft aria-hidden="true" size={18} />
        Back to analysis workspace
      </Link>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <form onSubmit={handleGenerate} className="surface h-fit rounded-3xl p-5 sm:p-7">
          <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
            Collect feedback first
          </p>
          <h1 className="mt-1 text-3xl font-semibold">Generate a policy consultation survey</h1>
          <p className="mt-3" style={{ color: "var(--muted-foreground)" }}>
            Add only the policy. PolicyPulse creates neutral questions ready for Google Forms.
          </p>

          <button
            type="button"
            onClick={() => {
              setPolicyText(SURVEY_DEMO_POLICY);
              setPolicyFile(null);
            }}
            className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-xl border px-4 font-semibold hover:bg-[var(--surface-subtle)]"
          >
            <ClipboardList aria-hidden="true" size={18} />
            Load sample policy
          </button>

          <label className="mt-5 flex min-h-24 items-center justify-center gap-3 rounded-2xl border border-dashed bg-[var(--surface-subtle)] px-4 text-center hover:border-[var(--primary)]">
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.rtf"
              className="sr-only"
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                setPolicyFile(event.target.files?.[0] ?? null)
              }
            />
            {policyFile ? <Check aria-hidden="true" size={19} /> : <UploadCloud aria-hidden="true" size={20} />}
            <span>
              <strong className="block">{policyFile?.name ?? "Choose policy file"}</strong>
              <span className="text-sm" style={{ color: "var(--muted-foreground)" }}>
                PDF, DOCX, TXT, MD, or RTF
              </span>
            </span>
          </label>

          <label htmlFor="survey-policy" className="mb-2 mt-5 block font-semibold">
            Policy text
          </label>
          <textarea
            id="survey-policy"
            rows={14}
            value={policyText}
            onChange={(event) => setPolicyText(event.target.value)}
            className="w-full resize-y rounded-2xl border bg-[var(--surface)] px-4 py-3 outline-none focus:border-[var(--focus)]"
            placeholder="Paste the proposed policy…"
          />

          {error && (
            <p role="alert" className="mt-4 rounded-xl bg-[var(--danger-soft)] p-3 text-sm text-[var(--danger)]">
              {error}
            </p>
          )}

          {loading && (
            <div className="mt-5 rounded-2xl border bg-[var(--surface-subtle)] p-4" aria-live="polite">
              <div className="flex items-center gap-3">
                <LoaderCircle className="animate-spin text-[var(--primary)]" aria-hidden="true" size={20} />
                <span className="font-semibold">{progress[progressIndex]}</span>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-5 inline-flex min-h-13 w-full items-center justify-center gap-2 rounded-xl bg-[var(--primary)] px-5 font-semibold text-[var(--on-primary)] disabled:opacity-60"
          >
            {loading ? <LoaderCircle className="animate-spin" aria-hidden="true" size={19} /> : <Send aria-hidden="true" size={19} />}
            Generate survey blueprint
          </button>
        </form>

        <section className="surface min-h-96 rounded-3xl p-5 sm:p-7">
          {!blueprint ? (
            <div className="grid min-h-[32rem] place-items-center text-center">
              <div className="max-w-md">
                <FileText className="mx-auto text-[var(--primary)]" aria-hidden="true" size={34} />
                <h2 className="mt-4 text-2xl font-semibold">Survey blueprint appears here</h2>
                <p className="mt-2" style={{ color: "var(--muted-foreground)" }}>
                  It will contain balanced questions, answer types, options, and respondent guidance.
                </p>
              </div>
            </div>
          ) : (
            <SurveyResult
              blueprint={blueprint}
              deployment={deployment}
              deploying={deploying}
              onDeploy={handleDeploy}
              onDownloadTemplate={() => void downloadTemplate()}
            />
          )}
        </section>
      </div>
    </main>
  );
}

function SurveyResult({
  blueprint,
  deployment,
  deploying,
  onDeploy,
  onDownloadTemplate,
}: {
  blueprint: SurveyBlueprint;
  deployment: GoogleFormDeployment | null;
  deploying: boolean;
  onDeploy: () => void;
  onDownloadTemplate: () => void;
}) {
  return (
    <div>
      <p className="text-sm font-semibold" style={{ color: "var(--primary)" }}>
        {blueprint.estimated_minutes}-minute consultation
      </p>
      <h2 className="mt-1 text-2xl font-semibold">{blueprint.title}</h2>
      <p className="mt-3" style={{ color: "var(--muted-foreground)" }}>
        {blueprint.description}
      </p>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onDeploy}
          disabled={deploying}
          className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-[var(--primary)] px-4 font-semibold text-[var(--on-primary)] disabled:opacity-60"
        >
          {deploying ? <LoaderCircle className="animate-spin" aria-hidden="true" size={18} /> : <ExternalLink aria-hidden="true" size={18} />}
          Create Google Form
        </button>
        <button
          type="button"
          onClick={onDownloadTemplate}
          className="inline-flex min-h-11 items-center gap-2 rounded-xl border px-4 font-semibold hover:bg-[var(--surface-subtle)]"
        >
          <Download aria-hidden="true" size={18} />
          Blank CSV template
        </button>
      </div>

      {deployment && (
        <div className="mt-5 rounded-2xl border bg-[var(--success-soft)] p-4">
          <p className="font-semibold text-[var(--success)]">{deployment.message}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <DeploymentLink href={deployment.form_url} label="Open live form" />
            <DeploymentLink href={deployment.edit_url} label="Edit form" />
            <DeploymentLink href={deployment.response_sheet_url} label="Response sheet" />
            <DeploymentLink href={deployment.csv_file_url} label="Live CSV file" />
            <DeploymentLink href={deployment.xlsx_export_url} label="Download Excel" />
          </div>
        </div>
      )}

      <div className="mt-7 space-y-6">
        {blueprint.sections.map((section, sectionIndex) => (
          <section key={section.title}>
            <h3 className="text-lg font-semibold">{section.title}</h3>
            {section.description && (
              <p className="mt-1 text-sm" style={{ color: "var(--muted-foreground)" }}>
                {section.description}
              </p>
            )}
            <div className="mt-3 space-y-3">
              {section.questions.map((question, questionIndex) => {
                const previousQuestions = blueprint.sections
                  .slice(0, sectionIndex)
                  .reduce((total, item) => total + item.questions.length, 0);
                const questionNumber = previousQuestions + questionIndex + 1;
                return (
                  <article key={question.id} className="rounded-2xl border bg-[var(--surface-subtle)] p-4">
                    <div className="flex items-start gap-3">
                      <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-[var(--primary-soft)] text-sm font-semibold text-[var(--primary-strong)]">
                        {questionNumber}
                      </span>
                      <div>
                        <p className="font-semibold">{question.question}</p>
                        <p className="mt-1 text-sm" style={{ color: "var(--muted-foreground)" }}>
                          {question.type.replaceAll("_", " ")} · {question.required ? "Required" : "Optional"}
                        </p>
                        {question.options.length > 0 && (
                          <ul className="mt-2 space-y-1 text-sm" style={{ color: "var(--muted-foreground)" }}>
                            {question.options.map((option) => (
                              <li key={option}>• {option}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      <div className="mt-7 rounded-2xl border bg-[var(--surface-subtle)] p-4">
        <div className="flex items-center gap-2">
          <FileSpreadsheet aria-hidden="true" size={19} style={{ color: "var(--primary)" }} />
          <h3 className="font-semibold">Sharing message</h3>
        </div>
        <p className="mt-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
          {blueprint.sharing_message}
        </p>
      </div>
    </div>
  );
}

function DeploymentLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border bg-[var(--surface)] px-3 text-sm font-semibold"
    >
      {label}
      <ExternalLink aria-hidden="true" size={14} />
    </a>
  );
}
