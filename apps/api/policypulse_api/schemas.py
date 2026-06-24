from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceType(StrEnum):
    POLICY = "policy"
    COMMENT = "comment"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(StrEnum):
    NICE_TO_HAVE = "nice-to-have"
    IMPORTANT = "important"
    CRITICAL = "critical"


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StageStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceItem(StrictModel):
    id: str = Field(pattern=r"^(POL|COM)-\d{3}$")
    type: SourceType
    text: str = Field(min_length=1)


class ParseResponse(StrictModel):
    policy_text: str = ""
    comments: list[str] = Field(default_factory=list)
    policy_paragraphs: list[SourceItem] = Field(default_factory=list)
    comment_sources: list[SourceItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    policy_metadata: dict[str, str | int | bool] = Field(default_factory=dict)
    comments_metadata: dict[str, str | int | bool] = Field(default_factory=dict)


class AnalysisRequest(StrictModel):
    policy_text: str = Field(min_length=20, max_length=50_000)
    comments: list[Annotated[str, Field(min_length=2, max_length=4_000)]] = Field(
        min_length=1,
        max_length=500,
    )
    demo: bool = False
    ingestion_warnings: list[str] = Field(default_factory=list, max_length=20)


class Sentiment(StrictModel):
    support: int = Field(ge=0, le=100)
    opposition: int = Field(ge=0, le=100)
    neutral: int = Field(ge=0, le=100)
    overall_mood: str

    @model_validator(mode="after")
    def percentages_total_100(self) -> Sentiment:
        if self.support + self.opposition + self.neutral != 100:
            raise ValueError("Sentiment percentages must total 100")
        return self


class CommentAssessment(StrictModel):
    comment_id: str = Field(pattern=r"^COM-\d{3}$")
    stance: Literal["support", "opposition", "neutral"]
    urgency: Literal["low", "medium", "high"]
    tone: str
    themes: list[str] = Field(min_length=1, max_length=3)
    affected_groups: list[str] = Field(default_factory=list)


class PolicyAnalysis(StrictModel):
    title: str
    summary: str
    main_rules: list[str]
    affected_groups: list[str]
    unclear_clauses: list[str]
    evidence_ids: list[str]


class Concern(StrictModel):
    id: str = Field(pattern=r"^CON-\d{3}$")
    theme: str
    summary: str
    count: int = Field(ge=1)
    percentage: float = Field(ge=0, le=100)
    urgency: Literal["low", "medium", "high"]
    evidence_ids: list[str]
    limited_evidence: bool = False


class Gap(StrictModel):
    id: str = Field(pattern=r"^GAP-\d{3}$")
    title: str
    description: str
    covered_in_policy: bool
    severity: Severity
    suggested_fix: str
    evidence_ids: list[str]
    concern_ids: list[str]
    limited_evidence: bool = False


class Recommendation(StrictModel):
    id: str = Field(pattern=r"^REC-\d{3}$")
    title: str
    action: str
    rationale: str
    priority: Priority
    gap_ids: list[str]
    evidence_ids: list[str]
    revised_wording: str | None = None
    limited_evidence: bool = False


class AnalysisResult(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    policy: PolicyAnalysis
    sentiment: Sentiment
    concerns: list[Concern]
    gaps: list[Gap]
    recommendations: list[Recommendation]
    executive_memo: str
    methodology: str
    limitations: list[str]
    ingestion_warnings: list[str] = Field(default_factory=list)
    sources: list[SourceItem]
    generated_at: datetime = Field(default_factory=utc_now)


class StageProgress(StrictModel):
    id: str
    label: str
    status: StageStatus = StageStatus.QUEUED
    message: str = "Waiting"


class AnalysisJob(StrictModel):
    id: str
    status: AnalysisStatus = AnalysisStatus.QUEUED
    stages: list[StageProgress]
    result: AnalysisResult | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AnalysisCreated(StrictModel):
    id: str
    status: AnalysisStatus


class EvidenceDetail(StrictModel):
    source: SourceItem
    related_finding: str


class ReportRequest(StrictModel):
    result: AnalysisResult
    format: Literal["markdown", "pdf"]


class ApiError(StrictModel):
    code: str
    message: str
    request_id: str | None = None


class SurveyQuestion(StrictModel):
    id: str = Field(pattern=r"^Q-\d{3}$")
    question: str = Field(min_length=5)
    type: Literal[
        "multiple_choice",
        "checkboxes",
        "linear_scale",
        "short_answer",
        "paragraph",
    ]
    options: list[str] = Field(default_factory=list)
    required: bool
    purpose: str
    scale_min: int | None = Field(default=None, ge=1, le=10)
    scale_max: int | None = Field(default=None, ge=2, le=10)
    scale_min_label: str | None = None
    scale_max_label: str | None = None

    @model_validator(mode="after")
    def validate_question_configuration(self) -> SurveyQuestion:
        if self.type in {"multiple_choice", "checkboxes"} and len(self.options) < 2:
            raise ValueError("Choice questions require at least two options")
        if self.type == "linear_scale":
            if self.scale_min is None or self.scale_max is None:
                raise ValueError("Linear scale questions require scale_min and scale_max")
            if self.scale_min >= self.scale_max:
                raise ValueError("scale_min must be lower than scale_max")
        return self


class SurveySection(StrictModel):
    title: str
    description: str = ""
    questions: list[SurveyQuestion] = Field(min_length=1)


class SurveyBlueprint(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    title: str
    description: str
    policy_summary: str
    sections: list[SurveySection] = Field(min_length=2)
    sharing_message: str
    estimated_minutes: int = Field(ge=2, le=20)
    generated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_question_count(self) -> SurveyBlueprint:
        count = sum(len(section.questions) for section in self.sections)
        if not 8 <= count <= 12:
            raise ValueError("Survey must contain 8 to 12 questions")
        return self


class SurveyRequest(StrictModel):
    policy_text: str = Field(min_length=20, max_length=50_000)


class GoogleFormRequest(StrictModel):
    blueprint: SurveyBlueprint


class GoogleFormDeployment(StrictModel):
    form_url: str
    edit_url: str
    response_sheet_url: str
    csv_file_url: str
    csv_export_url: str
    xlsx_export_url: str
    form_id: str
    spreadsheet_id: str
    message: str
