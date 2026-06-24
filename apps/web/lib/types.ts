export type SourceType = "policy" | "comment";
export type AnalysisStatus = "queued" | "running" | "completed" | "failed";
export type StageStatus = "queued" | "running" | "completed" | "failed";
export type Priority = "nice-to-have" | "important" | "critical";
export type Severity = "low" | "medium" | "high" | "critical";

export type SourceItem = {
  id: string;
  type: SourceType;
  text: string;
};

export type ParseResponse = {
  policy_text: string;
  comments: string[];
  policy_paragraphs: SourceItem[];
  comment_sources: SourceItem[];
  warnings: string[];
  policy_metadata: Record<string, string | number | boolean>;
  comments_metadata: Record<string, string | number | boolean>;
};

export type AnalysisRequest = {
  policy_text: string;
  comments: string[];
  demo: boolean;
  ingestion_warnings: string[];
};

export type Sentiment = {
  support: number;
  opposition: number;
  neutral: number;
  overall_mood: string;
};

export type PolicyAnalysis = {
  title: string;
  summary: string;
  main_rules: string[];
  affected_groups: string[];
  unclear_clauses: string[];
  evidence_ids: string[];
};

export type Concern = {
  id: string;
  theme: string;
  summary: string;
  count: number;
  percentage: number;
  urgency: "low" | "medium" | "high";
  evidence_ids: string[];
  limited_evidence: boolean;
};

export type Gap = {
  id: string;
  title: string;
  description: string;
  covered_in_policy: boolean;
  severity: Severity;
  suggested_fix: string;
  evidence_ids: string[];
  concern_ids: string[];
  limited_evidence: boolean;
};

export type Recommendation = {
  id: string;
  title: string;
  action: string;
  rationale: string;
  priority: Priority;
  gap_ids: string[];
  evidence_ids: string[];
  revised_wording: string | null;
  limited_evidence: boolean;
};

export type AnalysisResult = {
  schema_version: "1.0";
  policy: PolicyAnalysis;
  sentiment: Sentiment;
  concerns: Concern[];
  gaps: Gap[];
  recommendations: Recommendation[];
  executive_memo: string;
  methodology: string;
  limitations: string[];
  ingestion_warnings: string[];
  sources: SourceItem[];
  generated_at: string;
};

export type StageProgress = {
  id: string;
  label: string;
  status: StageStatus;
  message: string;
};

export type AnalysisJob = {
  id: string;
  status: AnalysisStatus;
  stages: StageProgress[];
  result: AnalysisResult | null;
  error: string | null;
  created_at: string;
  updated_at: string;
};

export type AnalysisCreated = {
  id: string;
  status: AnalysisStatus;
};

export type SurveyQuestion = {
  id: string;
  question: string;
  type: "multiple_choice" | "checkboxes" | "linear_scale" | "short_answer" | "paragraph";
  options: string[];
  required: boolean;
  purpose: string;
  scale_min: number | null;
  scale_max: number | null;
  scale_min_label: string | null;
  scale_max_label: string | null;
};

export type SurveySection = {
  title: string;
  description: string;
  questions: SurveyQuestion[];
};

export type SurveyBlueprint = {
  schema_version: "1.0";
  title: string;
  description: string;
  policy_summary: string;
  sections: SurveySection[];
  sharing_message: string;
  estimated_minutes: number;
  generated_at: string;
};

export type GoogleFormDeployment = {
  form_url: string;
  edit_url: string;
  response_sheet_url: string;
  csv_file_url: string;
  csv_export_url: string;
  xlsx_export_url: string;
  form_id: string;
  spreadsheet_id: string;
  message: string;
};
