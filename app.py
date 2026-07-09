from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from src.agents.pipeline import run_pipeline, run_survey_generation
from src.agents.survey_generator_agent import deploy_google_form, fetch_form_responses
from src.parsers.comment_parser import parse_comments_file, parse_comments_text
from src.parsers.file_parser import parse_policy_file
from src.utils.settings import get_secret

load_dotenv()

ROOT = Path(__file__).parent
SAMPLE_POLICY_PATH = ROOT / "sample_data" / "attendance_policy.txt"
SAMPLE_COMMENTS_PATH = ROOT / "sample_data" / "student_comments.csv"

st.set_page_config(
    page_title="PolicyPulse AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #07111f;
            --surface: #0d1b2a;
            --surface-soft: #11243a;
            --border: rgba(148, 163, 184, 0.18);
            --text: #e5eef9;
            --muted: #9db2c9;
            --primary: #3cb9ff;
            --primary-strong: #2596da;
            --success: #25c685;
            --warning: #f5b942;
            --danger: #ff6b81;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(60, 185, 255, 0.16), transparent 30%),
                radial-gradient(circle at top right, rgba(37, 198, 133, 0.10), transparent 26%),
                linear-gradient(180deg, #07111f 0%, #091522 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        .pp-hero {
            padding: 1.6rem 1.7rem;
            border: 1px solid var(--border);
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(13, 27, 42, 0.95), rgba(10, 22, 35, 0.92));
            box-shadow: 0 24px 50px rgba(0, 0, 0, 0.25);
            margin-bottom: 1rem;
        }

        .pp-eyebrow {
            color: var(--primary);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .pp-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: white;
            margin: 0.35rem 0 0.8rem 0;
            line-height: 1.1;
        }

        .pp-subtitle {
            color: var(--muted);
            font-size: 1rem;
            max-width: 62rem;
            line-height: 1.7;
        }

        .pp-card {
            border: 1px solid var(--border);
            border-radius: 22px;
            background: rgba(13, 27, 42, 0.88);
            box-shadow: 0 18px 38px rgba(0, 0, 0, 0.18);
            padding: 1rem 1.15rem 1.15rem 1.15rem;
        }

        .pp-card-title {
            color: white;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.1rem;
        }

        .pp-card-subtitle {
            color: var(--muted);
            font-size: 0.92rem;
            margin-bottom: 0.9rem;
        }

        .pp-metric {
            border: 1px solid var(--border);
            background: rgba(17, 36, 58, 0.9);
            border-radius: 18px;
            padding: 1rem;
        }

        .pp-metric-label {
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.3rem;
        }

        .pp-metric-value {
            color: white;
            font-size: 1.75rem;
            font-weight: 800;
            line-height: 1.1;
        }

        .pp-note {
            border-left: 4px solid var(--primary);
            background: rgba(60, 185, 255, 0.10);
            color: var(--text);
            border-radius: 14px;
            padding: 0.95rem 1rem;
            margin: 0.8rem 0;
        }

        .pp-warning {
            border-left-color: var(--warning);
            background: rgba(245, 185, 66, 0.10);
        }

        .pp-danger {
            border-left-color: var(--danger);
            background: rgba(255, 107, 129, 0.10);
        }

        .pp-list {
            margin: 0;
            padding-left: 1.2rem;
            color: var(--text);
            line-height: 1.7;
        }

        .pp-pill {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-right: 0.4rem;
            margin-bottom: 0.3rem;
            border: 1px solid transparent;
        }

        .pp-pill-primary { background: rgba(60, 185, 255, 0.15); color: #95dcff; border-color: rgba(60,185,255,0.25); }
        .pp-pill-success { background: rgba(37, 198, 133, 0.15); color: #8ef0c2; border-color: rgba(37,198,133,0.25); }
        .pp-pill-warning { background: rgba(245, 185, 66, 0.15); color: #ffd37d; border-color: rgba(245,185,66,0.25); }
        .pp-pill-danger { background: rgba(255, 107, 129, 0.15); color: #ffb4c0; border-color: rgba(255,107,129,0.25); }

        div[data-testid="stFileUploader"] {
            background: rgba(17, 36, 58, 0.55);
            border-radius: 18px;
            padding: 0.5rem;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
            background: rgba(7, 17, 31, 0.85);
            color: white;
            border-radius: 16px;
        }

        div[data-testid="stTabs"] button {
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_demo_data() -> tuple[str, str]:
    policy = SAMPLE_POLICY_PATH.read_text(encoding="utf-8")
    df = pd.read_csv(SAMPLE_COMMENTS_PATH)
    comments = "\n".join(df["comment"].dropna().astype(str).tolist())
    return policy, comments


def init_state() -> None:
    demo_policy, demo_comments = load_demo_data()
    defaults = {
        "policy_text": "",
        "comments_text": "",
        "analysis_results": None,
        "survey_results": None,
        "google_form_id": "",
        "show_analysis_success": False,
        "show_survey_success": False,
        "demo_policy": demo_policy,
        "demo_comments": demo_comments,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def read_policy_input(uploaded_file, pasted_text: str) -> str:
    if uploaded_file is not None:
        return parse_policy_file(uploaded_file)
    return pasted_text.strip()


def read_comments_input(uploaded_file, pasted_text: str) -> list[str]:
    if uploaded_file is not None:
        return parse_comments_file(uploaded_file)
    return parse_comments_text(pasted_text)


def build_markdown_report(result: dict) -> str:
    policy = result["policy_analysis"]
    sentiment = result["sentiment_analysis"]
    concerns = result["concern_analysis"]
    gaps = result["gap_analysis"]
    recommendations = result["recommendations"]
    lines: list[str] = []
    lines.append(f"# {policy.get('policy_title', 'Policy Analysis Report')}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(recommendations.get("executive_memo", "No memo available."))
    lines.append("")
    lines.append("## Policy Structure")
    for item in policy.get("main_rules", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Sentiment")
    lines.append(
        f"- Support: {sentiment.get('support_percentage', 0)}% | "
        f"Opposition: {sentiment.get('opposition_percentage', 0)}% | "
        f"Neutral: {sentiment.get('neutral_percentage', 0)}%"
    )
    lines.append(f"- Overall mood: {sentiment.get('overall_mood', 'Unknown')}")
    lines.append("")
    lines.append("## Concern Clusters")
    for concern in concerns.get("concern_clusters", []):
        lines.append(f"- {concern.get('theme', 'Theme')} ({concern.get('count', 0)} comments)")
    lines.append("")
    lines.append("## Policy Gaps")
    for gap in gaps.get("gaps", []):
        status = "Covered" if gap.get("covered_in_policy") else "Missing"
        lines.append(f"- {gap.get('concern', 'Concern')}: {status} — {gap.get('gap_description', '')}")
    lines.append("")
    lines.append("## Recommendations")
    for item in recommendations.get("recommendations", []):
        lines.append(f"- [{item.get('priority', 'Priority')}] {item.get('action', '')}")
    return "\n".join(lines)


def render_metric(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="pp-metric">
            <div class="pp-metric-label">{label}</div>
            <div class="pp-metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, tone: str = "primary") -> str:
    return f'<span class="pp-pill pp-pill-{tone}">{text}</span>'


def render_sidebar() -> None:
    api_key_configured = bool(get_secret("GROQ_API_KEY"))
    google_forms_configured = bool(get_secret("GOOGLE_SCRIPT_URL"))

    st.sidebar.markdown("## PolicyPulse AI")
    st.sidebar.caption("Deployment-ready consultation workspace")
    st.sidebar.markdown(
        pill("Groq connected" if api_key_configured else "Groq missing", "success" if api_key_configured else "danger")
        + pill(
            "Google Forms enabled" if google_forms_configured else "Google Forms optional",
            "primary" if google_forms_configured else "warning",
        ),
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Load verified sample", use_container_width=True):
        st.session_state["policy_text"] = st.session_state["demo_policy"]
        st.session_state["comments_text"] = st.session_state["demo_comments"]
        st.toast("Verified sample loaded.", icon="✨")

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "This Streamlit version is optimized for demo deployment with uploads, analysis tabs, survey generation, and export-friendly outputs."
    )


def run_analysis_workflow(policy_text: str, comments: list[str]) -> dict:
    with st.status("Running multi-agent analysis", expanded=True) as status:
        status.write("1. Extracting policy structure")
        status.write("2. Aggregating stakeholder sentiment")
        status.write("3. Clustering major concerns")
        status.write("4. Detecting policy gaps")
        status.write("5. Generating recommendations and executive memo")
        result = run_pipeline(policy_text, comments)
        status.update(label="Analysis completed", state="complete")
        return result


def run_survey_workflow(policy_text: str) -> dict:
    with st.status("Generating survey blueprint", expanded=True) as status:
        status.write("1. Summarizing the policy context")
        status.write("2. Drafting consultation questions")
        status.write("3. Structuring a Google-Forms-ready blueprint")
        result = run_survey_generation(policy_text)
        status.update(label="Survey blueprint completed", state="complete")
        return result


def render_overview(result: dict) -> None:
    policy = result["policy_analysis"]
    sentiment = result["sentiment_analysis"]
    concerns = result["concern_analysis"].get("concern_clusters", [])
    gaps = result["gap_analysis"].get("gaps", [])
    recommendations = result["recommendations"]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric("Comments analyzed", str(sum(item.get("count", 0) for item in concerns)))
    with m2:
        render_metric("Top concerns", str(len(concerns)))
    with m3:
        critical_count = sum(
            1 for item in recommendations.get("recommendations", []) if item.get("priority", "").lower() == "critical"
        )
        render_metric("Critical actions", str(critical_count))
    with m4:
        render_metric("Overall mood", sentiment.get("overall_mood", "Unknown"))

    st.markdown(
        f"""
        <div class="pp-card" style="margin-top: 1rem;">
            <div class="pp-card-title">{policy.get("policy_title", "Policy report")}</div>
            <div class="pp-card-subtitle">Structured policy extraction with evidence-informed public feedback synthesis.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns((1.1, 0.9))
    with c1:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=["Support", "Opposition", "Neutral"],
                    y=[
                        sentiment.get("support_percentage", 0),
                        sentiment.get("opposition_percentage", 0),
                        sentiment.get("neutral_percentage", 0),
                    ],
                    marker_color=["#25c685", "#ff6b81", "#3cb9ff"],
                )
            ]
        )
        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e5eef9",
            yaxis_title="Percentage",
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### Extracted policy structure")
        st.markdown("**Main rules**")
        st.markdown("\n".join(f"- {item}" for item in policy.get("main_rules", [])) or "- No rules extracted")
        if policy.get("affected_groups"):
            st.markdown("**Affected groups**")
            st.markdown("\n".join(f"- {item}" for item in policy.get("affected_groups", [])))
        if policy.get("unclear_clauses"):
            st.markdown("**Unclear clauses**")
            st.markdown("\n".join(f"- {item}" for item in policy.get("unclear_clauses", [])))

    if gaps:
        st.markdown('<div class="pp-note">Large submissions or heavy live usage may take longer because the Streamlit deployment runs the full multi-agent workflow directly.</div>', unsafe_allow_html=True)


def render_concerns(result: dict) -> None:
    concerns = result["concern_analysis"].get("concern_clusters", [])
    if not concerns:
        st.info("No concern clusters available yet.")
        return
    for concern in concerns:
        urgency = concern.get("urgency_level", "Medium").lower()
        tone = "danger" if urgency == "high" else "warning" if urgency == "medium" else "success"
        st.markdown(
            f"""
            <div class="pp-card" style="margin-bottom: 0.9rem;">
                <div class="pp-card-title">{concern.get('theme', 'Concern')}</div>
                <div>{pill(f"{concern.get('count', 0)} comments", "primary")} {pill(concern.get('urgency_level', 'Medium') + " urgency", tone)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**Evidence comments**")
        for sample in concern.get("sample_comments", [])[:3]:
            st.markdown(f"- {sample}")


def render_gaps(result: dict) -> None:
    gaps = result["gap_analysis"].get("gaps", [])
    if not gaps:
        st.info("No policy gaps available yet.")
        return
    for gap in gaps:
        covered = bool(gap.get("covered_in_policy"))
        st.markdown(
            f"""
            <div class="pp-card" style="margin-bottom: 0.9rem;">
                <div class="pp-card-title">{gap.get('concern', 'Policy gap')}</div>
                <div>{pill('Covered' if covered else 'Missing', 'success' if covered else 'danger')}</div>
                <p style="color:#9db2c9; margin-top:0.8rem;">{gap.get('gap_description', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_recommendations(result: dict) -> None:
    recommendations = result["recommendations"]
    items = recommendations.get("recommendations", [])
    cols = st.columns(3)
    grouped = {
        "Critical": [],
        "Important": [],
        "Nice-to-have": [],
    }
    for item in items:
        grouped.setdefault(item.get("priority", "Important"), []).append(item.get("action", ""))

    for col, priority, tone in zip(cols, ["Critical", "Important", "Nice-to-have"], ["danger", "warning", "primary"]):
        with col:
            st.markdown(
                f"""
                <div class="pp-card">
                    <div class="pp-card-title">{priority}</div>
                    <div>{pill(priority, tone)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for action in grouped.get(priority, []) or ["No items in this category."]:
                st.markdown(f"- {action}")

    revised = recommendations.get("revised_policy_suggestions", [])
    questions = recommendations.get("meeting_questions", [])
    if revised:
        st.markdown("### Suggested wording updates")
        for item in revised:
            st.markdown(f"- {item}")
    if questions:
        st.markdown("### Stakeholder meeting questions")
        for item in questions:
            st.markdown(f"- {item}")


def render_memo(result: dict) -> None:
    memo = result["recommendations"].get("executive_memo", "Executive memo not available.")
    st.markdown(
        f"""
        <div class="pp-card">
            <div class="pp-card-title">Executive memo</div>
            <div class="pp-card-subtitle">Concise leadership-ready summary generated from the policy and public feedback.</div>
            <div style="color:#e5eef9; line-height:1.8;">{memo.replace(chr(10), '<br><br>')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pp-note pp-warning">🤖 This public deployment is intended for showcase usage. During heavier usage, live provider limits can occasionally slow or interrupt analysis runs.</div>',
        unsafe_allow_html=True,
    )


def render_survey(result: dict) -> None:
    survey = result if "sections" in result else result.get("survey", {})
    if not survey:
        st.info("No survey blueprint available yet.")
        return

    st.markdown(
        f"""
        <div class="pp-card">
            <div class="pp-card-title">{survey.get('title', 'Survey blueprint')}</div>
            <div class="pp-card-subtitle">{survey.get('description', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for section in survey.get("sections", []):
        st.markdown(f"### {section.get('section_name', 'Section')}")
        for question in section.get("questions", []):
            question_type = question.get("type", "text")
            st.markdown(
                f"- **{question.get('question', '')}** {pill(question_type.replace('_', ' ').title(), 'primary')}",
                unsafe_allow_html=True,
            )
            options = question.get("options", [])
            if options:
                st.caption("Options: " + ", ".join(options))

    steps = survey.get("google_forms_steps", [])
    if steps:
        st.markdown("### Manual Google Forms setup")
        for step in steps:
            st.markdown(f"- {step}")

    if st.button("Deploy survey to Google Forms", use_container_width=True):
        with st.spinner("Creating Google Form..."):
            deployment = deploy_google_form(survey)
        if deployment.get("error"):
            st.error(deployment["error"])
        else:
            st.success("Google Form created successfully.")
            st.markdown(f"- **Live form:** {deployment.get('url')}")
            if deployment.get("edit_url"):
                st.markdown(f"- **Edit form:** {deployment.get('edit_url')}")
            if deployment.get("form_id"):
                st.session_state["google_form_id"] = deployment["form_id"]


def main() -> None:
    inject_styles()
    init_state()
    render_sidebar()

    st.markdown(
        """
        <div class="pp-hero">
            <div class="pp-eyebrow">Policy consultation intelligence</div>
            <div class="pp-title">Turn policy uploads and stakeholder comments into actionable decisions.</div>
            <div class="pp-subtitle">
                This Streamlit deployment now follows the newer product experience: upload evidence, run the multi-agent pipeline,
                review concerns and policy gaps in tabs, generate a survey blueprint, and share a leadership-ready executive memo.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not get_secret("GROQ_API_KEY"):
        st.markdown(
            '<div class="pp-note pp-danger">⚠️ Groq API key is missing. Add <code>GROQ_API_KEY</code> in Streamlit secrets before running live analysis.</div>',
            unsafe_allow_html=True,
        )

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="pp-card-title">Policy document</div><div class="pp-card-subtitle">Upload PDF, DOCX, or TXT — or paste the policy directly.</div>', unsafe_allow_html=True)
        policy_file = st.file_uploader("Upload policy", type=["pdf", "docx", "txt"], key="policy_upload")
        policy_text = st.text_area(
            "Policy text",
            value=st.session_state["policy_text"],
            height=320,
            placeholder="Paste the draft policy here...",
        )
        st.session_state["policy_text"] = policy_text

    with right:
        st.markdown('<div class="pp-card-title">Public / stakeholder comments</div><div class="pp-card-subtitle">Upload CSV or TXT — or paste one comment per line.</div>', unsafe_allow_html=True)
        comments_file = st.file_uploader("Upload comments", type=["csv", "txt"], key="comments_upload")
        comments_text = st.text_area(
            "Comments",
            value=st.session_state["comments_text"],
            height=320,
            placeholder="Paste one comment per line...",
        )
        st.session_state["comments_text"] = comments_text

    fetch_col, analyze_col, survey_col = st.columns([1.25, 1, 1], gap="medium")
    with fetch_col:
        st.markdown("**Optional: sync comments from Google Forms**")
        form_id = st.text_input("Google Form ID", value=st.session_state["google_form_id"], placeholder="Enter form ID")
        st.session_state["google_form_id"] = form_id
        if st.button("Fetch Google Form responses", use_container_width=True):
            if not form_id.strip():
                st.warning("Enter a valid Google Form ID first.")
            else:
                with st.spinner("Fetching responses..."):
                    fetched = fetch_form_responses(form_id.strip())
                if fetched.get("error"):
                    st.error(fetched["error"])
                else:
                    csv_text = fetched.get("csv", "")
                    df = pd.read_csv(io.StringIO(csv_text))
                    source_col = next((col for col in df.columns if col.lower().strip() in {"comment", "comments", "feedback", "response", "responses"}), df.columns[0])
                    st.session_state["comments_text"] = "\n".join(df[source_col].dropna().astype(str).tolist())
                    st.success(f"Loaded {len(df[source_col].dropna())} responses from Google Forms.")
                    st.rerun()

    with analyze_col:
        analyze_clicked = st.button("Analyze policy", type="primary", use_container_width=True)

    with survey_col:
        survey_clicked = st.button("Generate survey blueprint", use_container_width=True)

    if analyze_clicked:
        try:
            policy_input = read_policy_input(policy_file, st.session_state["policy_text"])
            comment_input = read_comments_input(comments_file, st.session_state["comments_text"])
            if not policy_input:
                st.error("Please provide a policy document before running the analysis.")
            elif not comment_input:
                st.error("Please provide stakeholder comments before running the analysis.")
            else:
                result = run_analysis_workflow(policy_input, comment_input)
                st.session_state["analysis_results"] = result
                st.session_state["survey_results"] = result.get("survey")
                st.success("Analysis completed successfully.")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")

    if survey_clicked:
        try:
            policy_input = read_policy_input(policy_file, st.session_state["policy_text"])
            if not policy_input:
                st.error("Please provide a policy document before generating a survey.")
            else:
                survey = run_survey_workflow(policy_input)
                st.session_state["survey_results"] = survey
                st.success("Survey blueprint generated successfully.")
        except Exception as exc:
            st.error(f"Survey generation failed: {exc}")

    result = st.session_state.get("analysis_results")
    survey_result = st.session_state.get("survey_results")

    if result is None and survey_result is None:
        st.markdown(
            '<div class="pp-note">Use the verified sample from the sidebar or upload your own policy and comments to start a live run.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown("---")

    if result is not None:
        report_md = build_markdown_report(result)
        st.download_button(
            "Download Markdown report",
            data=report_md,
            file_name="policypulse-report.md",
            mime="text/markdown",
            use_container_width=False,
        )

        tabs = st.tabs(
            [
                "Overview",
                "Public concerns",
                "Policy gaps",
                "Recommendations",
                "Executive memo",
                "Survey blueprint",
            ]
        )
        with tabs[0]:
            render_overview(result)
        with tabs[1]:
            render_concerns(result)
        with tabs[2]:
            render_gaps(result)
        with tabs[3]:
            render_recommendations(result)
        with tabs[4]:
            render_memo(result)
        with tabs[5]:
            render_survey(result)
    elif survey_result is not None:
        render_survey(survey_result)


if __name__ == "__main__":
    main()
