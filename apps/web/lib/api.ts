import type {
  AnalysisCreated,
  AnalysisJob,
  AnalysisRequest,
  AnalysisResult,
  GoogleFormDeployment,
  ParseResponse,
  SurveyBlueprint,
} from "@/lib/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  return fallback;
}

async function requestJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(extractErrorMessage(payload, `Request failed with status ${response.status}`));
  }
  return (await response.json()) as T;
}

export async function parseInputs(form: FormData): Promise<ParseResponse> {
  const response = await fetch(`${API_URL}/v1/parse`, {
    method: "POST",
    body: form,
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(extractErrorMessage(payload, `Parse failed with status ${response.status}`));
  }
  return (await response.json()) as ParseResponse;
}

export async function createAnalysis(payload: AnalysisRequest): Promise<AnalysisCreated> {
  return requestJson<AnalysisCreated>(`${API_URL}/v1/analyses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getAnalysis(id: string): Promise<AnalysisJob> {
  return requestJson<AnalysisJob>(`${API_URL}/v1/analyses/${id}`);
}

export async function exportReport(result: AnalysisResult, format: "markdown" | "pdf"): Promise<Blob> {
  const response = await fetch(`${API_URL}/v1/reports/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ result, format }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(extractErrorMessage(payload, `Export failed with status ${response.status}`));
  }
  return await response.blob();
}

export async function parsePolicy(form: FormData): Promise<ParseResponse> {
  const response = await fetch(`${API_URL}/v1/policies/parse`, {
    method: "POST",
    body: form,
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(extractErrorMessage(payload, `Parse failed with status ${response.status}`));
  }
  return (await response.json()) as ParseResponse;
}

export async function generateSurvey(policyText: string): Promise<SurveyBlueprint> {
  return requestJson<SurveyBlueprint>(`${API_URL}/v1/surveys/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ policy_text: policyText }),
  });
}

export async function createGoogleForm(blueprint: SurveyBlueprint): Promise<GoogleFormDeployment> {
  return requestJson<GoogleFormDeployment>(`${API_URL}/v1/surveys/google-form`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ blueprint }),
  });
}

export async function exportSurveyTemplate(blueprint: SurveyBlueprint): Promise<Blob> {
  const response = await fetch(`${API_URL}/v1/surveys/response-template`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ blueprint }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(extractErrorMessage(payload, `Export failed with status ${response.status}`));
  }
  return await response.blob();
}

export function presentApiError(error: unknown): string {
  const message = error instanceof Error ? error.message : "The request could not be completed.";
  const normalized = message.toLowerCase();

  if (normalized.includes("failed to fetch")) {
    return "🌐 We could not reach the live analysis service just now. Please confirm the deployed API is available and try again.";
  }
  if (
    normalized.includes("rate limit") ||
    normalized.includes("too many requests") ||
    normalized.includes("request too large") ||
    normalized.includes("tokens per minute") ||
    normalized.includes("permission-denied") ||
    normalized.includes("credits") ||
    normalized.includes("service tier")
  ) {
    return "🤖 Our live AI helper needs a short coffee break — this showcase deployment has temporarily hit provider usage or quota limits. Please try again shortly, reduce the submission size, or use the verified sample.";
  }
  if (normalized.includes("timed out") || normalized.includes("timeout")) {
    return "⏳ The live analysis took a little too long this time. Please try again in a moment or submit a smaller document set.";
  }
  return message;
}
