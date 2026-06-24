from .schemas import (
    AnalysisResult,
    Concern,
    Gap,
    PolicyAnalysis,
    Priority,
    Recommendation,
    Sentiment,
    Severity,
)
from .sources import create_comment_sources, split_policy_paragraphs

DEMO_POLICY = """University Attendance and Academic Participation Policy

Students must maintain at least 85% attendance in every enrolled course. A student whose
attendance falls below 85% will not be permitted to sit the final examination for that course.

Faculty members are responsible for recording attendance and reporting shortages before final
examinations. The policy takes effect at the beginning of the next academic term.

The university may review exceptional cases at its discretion."""

DEMO_COMMENTS = [
    "Attendance matters, but an automatic exam ban is too harsh without an appeal.",
    "Working students need limited flexibility when shifts cannot be changed.",
    "There must be a documented medical exemption for hospitalization and chronic illness.",
    "Students with disabilities need reasonable accommodations rather than discretionary exceptions.",
    "Public transport delays make an inflexible 85 percent threshold unfair for commuters.",
    "I support stronger attendance because students learn more when they attend class.",
    "Who corrects the record when a lecturer marks a student absent by mistake?",
    "The university should warn students early and provide an appeal deadline.",
    "Medical documents should be reviewed consistently across departments.",
    "The rule is useful, but exceptions and dispute handling must be clearly written.",
]


def build_demo_result() -> AnalysisResult:
    policy_sources = split_policy_paragraphs(DEMO_POLICY)
    comment_sources = create_comment_sources(DEMO_COMMENTS)
    return AnalysisResult(
        policy=PolicyAnalysis(
            title="University Attendance and Academic Participation Policy",
            summary=(
                "The proposal requires 85% attendance in every course and blocks students below "
                "the threshold from final examinations. It delegates recording to faculty but "
                "leaves exceptions and review procedures largely undefined."
            ),
            main_rules=[
                "Maintain at least 85% attendance in every enrolled course.",
                "Students below the threshold cannot sit the final examination.",
                "Faculty record attendance and report shortages.",
            ],
            affected_groups=["All enrolled students", "Faculty members", "Academic administration"],
            unclear_clauses=[
                "No defined appeal or attendance-correction process.",
                "Exceptional-case review is discretionary and has no eligibility standard.",
            ],
            evidence_ids=["POL-002", "POL-003", "POL-004"],
        ),
        sentiment=Sentiment(support=20, opposition=50, neutral=30, overall_mood="Concerned but constructive"),
        concerns=[
            Concern(
                id="CON-001",
                theme="Appeals and record correction",
                summary="Students want a predictable route to challenge errors or exceptional decisions.",
                count=4,
                percentage=40,
                urgency="high",
                evidence_ids=["COM-001", "COM-007", "COM-008", "COM-010"],
            ),
            Concern(
                id="CON-002",
                theme="Medical and disability accommodations",
                summary="The policy does not define consistent health-related exemptions or accommodations.",
                count=3,
                percentage=30,
                urgency="high",
                evidence_ids=["COM-003", "COM-004", "COM-009"],
            ),
            Concern(
                id="CON-003",
                theme="Working and commuting students",
                summary="Rigid enforcement may disproportionately affect workers and long-distance commuters.",
                count=2,
                percentage=20,
                urgency="medium",
                evidence_ids=["COM-002", "COM-005"],
            ),
            Concern(
                id="CON-004",
                theme="Support for attendance standards",
                summary="A minority supports stronger attendance expectations as an academic discipline measure.",
                count=1,
                percentage=10,
                urgency="low",
                evidence_ids=["COM-006"],
                limited_evidence=True,
            ),
        ],
        gaps=[
            Gap(
                id="GAP-001",
                title="No formal appeal or correction process",
                description=(
                    "The proposal imposes a high-impact penalty without defining notice, evidence review, or appeal."
                ),
                covered_in_policy=False,
                severity=Severity.CRITICAL,
                suggested_fix="Add written notice, record correction, appeal deadlines, and an independent reviewer.",
                evidence_ids=["POL-002", "POL-004", "COM-001", "COM-007", "COM-008"],
                concern_ids=["CON-001"],
            ),
            Gap(
                id="GAP-002",
                title="Undefined medical and disability protections",
                description=(
                    "Discretionary exceptional review does not establish accessible or consistent accommodations."
                ),
                covered_in_policy=False,
                severity=Severity.CRITICAL,
                suggested_fix=(
                    "Define medical exemptions and a disability-accommodation pathway with privacy safeguards."
                ),
                evidence_ids=["POL-004", "COM-003", "COM-004", "COM-009"],
                concern_ids=["CON-002"],
            ),
            Gap(
                id="GAP-003",
                title="No proportional flexibility mechanism",
                description="The policy does not address documented work or transport disruption.",
                covered_in_policy=False,
                severity=Severity.HIGH,
                suggested_fix="Permit limited, documented flexibility with equivalent participation requirements.",
                evidence_ids=["POL-002", "COM-002", "COM-005"],
                concern_ids=["CON-003"],
            ),
        ],
        recommendations=[
            Recommendation(
                id="REC-001",
                title="Create a transparent appeal pathway",
                action="Publish notice, correction, and appeal stages with clear deadlines and decision ownership.",
                rationale="The final-exam restriction is consequential and requires procedural fairness.",
                priority=Priority.CRITICAL,
                gap_ids=["GAP-001"],
                evidence_ids=["POL-002", "COM-001", "COM-007", "COM-008"],
                revised_wording=(
                    "Students must receive written notice of an attendance shortage and may request "
                    "record correction within five working days or appeal an adverse decision within ten."
                ),
            ),
            Recommendation(
                id="REC-002",
                title="Define health and accessibility protections",
                action="Create consistent medical-exemption and disability-accommodation standards.",
                rationale="Case-by-case discretion can produce inconsistent and inaccessible outcomes.",
                priority=Priority.CRITICAL,
                gap_ids=["GAP-002"],
                evidence_ids=["POL-004", "COM-003", "COM-004", "COM-009"],
                revised_wording=(
                    "Documented medical circumstances and approved disability accommodations shall be "
                    "assessed through a confidential, published process and may modify attendance requirements."
                ),
            ),
            Recommendation(
                id="REC-003",
                title="Introduce proportionate flexibility",
                action="Allow limited alternatives for verified work or transport disruption.",
                rationale="A narrow flexibility mechanism protects affected groups without removing the standard.",
                priority=Priority.IMPORTANT,
                gap_ids=["GAP-003"],
                evidence_ids=["COM-002", "COM-005", "COM-006"],
            ),
        ],
        executive_memo=(
            "The proposed attendance policy has a clear academic objective, and some students support "
            "stronger participation standards. However, the consultation identifies material procedural "
            "and accessibility gaps that should be resolved before implementation.\n\n"
            "Leadership should retain the attendance expectation while adding formal notice and appeal "
            "rights, consistent medical and disability protections, and narrowly defined flexibility for "
            "documented disruption. These changes would make enforcement more predictable, proportionate, "
            "and defensible without weakening the policy's central goal."
        ),
        methodology=(
            "PolicyPulse indexed policy paragraphs and comments, then used specialized analysis stages "
            "for extraction, sentiment, concern clustering, gap detection, and recommendations."
        ),
        limitations=[
            "AI-generated analysis should be reviewed by a qualified human decision-maker.",
            "Comment frequency describes this dataset and is not representative polling.",
            "This report is not legal advice.",
        ],
        ingestion_warnings=[],
        sources=[*policy_sources, *comment_sources],
    )
