from __future__ import annotations

from io import BytesIO
from textwrap import wrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .schemas import AnalysisResult


def build_markdown(result: AnalysisResult) -> str:
    lines = [
        "# PolicyPulse AI Consultation Report",
        "",
        f"Generated: {result.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Policy overview",
        "",
        f"**{result.policy.title}**",
        "",
        result.policy.summary,
        "",
        "## Sentiment",
        "",
        f"- Support: {result.sentiment.support}%",
        f"- Opposition: {result.sentiment.opposition}%",
        f"- Neutral or mixed: {result.sentiment.neutral}%",
        f"- Overall mood: {result.sentiment.overall_mood}",
        "",
        "## Public concerns",
        "",
    ]
    for concern in result.concerns:
        evidence = ", ".join(concern.evidence_ids) or "Limited evidence"
        lines.extend(
            [
                f"### {concern.theme} ({concern.percentage:.0f}%)",
                concern.summary,
                f"Evidence: {evidence}",
                "",
            ]
        )
    lines.extend(["## Policy gaps", ""])
    for gap in result.gaps:
        lines.extend(
            [
                f"### [{gap.severity.value.upper()}] {gap.title}",
                gap.description,
                f"Suggested fix: {gap.suggested_fix}",
                f"Evidence: {', '.join(gap.evidence_ids)}",
                "",
            ]
        )
    lines.extend(["## Recommendations", ""])
    for recommendation in result.recommendations:
        lines.extend(
            [
                f"### [{recommendation.priority.value.upper()}] {recommendation.title}",
                recommendation.action,
                f"Rationale: {recommendation.rationale}",
                f"Evidence: {', '.join(recommendation.evidence_ids)}",
                "",
            ]
        )
        if recommendation.revised_wording:
            lines.extend([f"> Suggested wording: {recommendation.revised_wording}", ""])
    lines.extend(
        [
            "## Executive memo",
            "",
            result.executive_memo,
            "",
            "## Methodology and limitations",
            "",
            result.methodology,
            "",
            *[f"- Ingestion warning: {warning}" for warning in result.ingestion_warnings],
            *[f"- {limitation}" for limitation in result.limitations],
        ]
    )
    return "\n".join(lines)


def build_pdf(result: AnalysisResult) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="PolicyPulse AI Consultation Report",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="PolicyPulseTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_LEFT,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#0369A1"),
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 15

    story = [
        Paragraph("PolicyPulse AI", styles["PolicyPulseTitle"]),
        Paragraph("Evidence-first public consultation report", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph(result.policy.title, styles["Section"]),
        Paragraph(result.policy.summary, styles["BodyText"]),
        Spacer(1, 12),
    ]
    sentiment_data = [
        ["Support", "Opposition", "Neutral / mixed"],
        [
            f"{result.sentiment.support}%",
            f"{result.sentiment.opposition}%",
            f"{result.sentiment.neutral}%",
        ],
    ]
    table = Table(sentiment_data, colWidths=[52 * mm, 52 * mm, 52 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0F2FE")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#075985")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BAE6FD")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([table, Paragraph("Public concerns", styles["Section"])])
    for concern in result.concerns:
        story.extend(
            [
                Paragraph(
                    f"<b>{concern.theme}</b> — {concern.percentage:.0f}% of comments",
                    styles["BodyText"],
                ),
                Paragraph(concern.summary, styles["BodyText"]),
                Paragraph(f"Evidence: {', '.join(concern.evidence_ids)}", styles["Italic"]),
                Spacer(1, 7),
            ]
        )
    story.append(Paragraph("Policy gaps", styles["Section"]))
    for gap in result.gaps:
        story.extend(
            [
                Paragraph(f"<b>{gap.severity.value.upper()}: {gap.title}</b>", styles["BodyText"]),
                Paragraph(gap.description, styles["BodyText"]),
                Paragraph(f"<b>Suggested fix:</b> {gap.suggested_fix}", styles["BodyText"]),
                Spacer(1, 7),
            ]
        )
    story.extend([PageBreak(), Paragraph("Recommendations", styles["Section"])])
    for recommendation in result.recommendations:
        story.extend(
            [
                Paragraph(
                    f"<b>{recommendation.priority.value.upper()}: {recommendation.title}</b>",
                    styles["BodyText"],
                ),
                Paragraph(recommendation.action, styles["BodyText"]),
                Paragraph(f"<b>Rationale:</b> {recommendation.rationale}", styles["BodyText"]),
                Spacer(1, 8),
            ]
        )
    story.extend(
        [
            Paragraph("Executive memo", styles["Section"]),
            *[Paragraph(paragraph, styles["BodyText"]) for paragraph in result.executive_memo.split("\n\n")],
            Paragraph("Methodology and limitations", styles["Section"]),
            Paragraph(result.methodology, styles["BodyText"]),
            *[
                Paragraph(f"• Ingestion warning: {warning}", styles["BodyText"])
                for warning in result.ingestion_warnings
            ],
            *[
                Paragraph(f"• {line}", styles["BodyText"])
                for limitation in result.limitations
                for line in wrap(limitation, 105)
            ],
        ]
    )
    document.build(story)
    return buffer.getvalue()
