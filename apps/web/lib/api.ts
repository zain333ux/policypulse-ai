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

async function requestJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
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
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Parse failed with status ${response.status}`);
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
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Export failed with status ${response.status}`);
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
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Parse failed with status ${response.status}`);
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
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Export failed with status ${response.status}`);
  }
  return await response.blob();
}
