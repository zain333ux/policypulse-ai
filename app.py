from __future__ import annotations

import io
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
            --bg: #07111a;
            --bg-soft: #0d1726;
            --surface: rgba(12, 23, 38, 0.88);
            --surface-strong: rgba(13, 27, 43, 0.96);
            --surface-muted: rgba(18, 35, 56, 0.72);
            --border: rgba(140, 170, 210, 0.18);
            --border-strong: rgba(118, 171, 255, 0.24);
            --text: #eff5ff;
            --muted: #a7bad5;
            --primary: #63b4ff;
            --primary-strong: #388bff;
            --accent: #7bf0c5;
            --warning: #f3bf62;
            --danger: #ff8fa8;
            --shadow: 0 20px 60px rgba(0, 0, 0, 0.26);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(78, 145, 255, 0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(123, 240, 197, 0.10), transparent 24%),
                linear-gradient(180deg, #06111c 0%, #08131f 48%, #091522 100%);
            color: var(--text);
        }

        .block-container {
            max-width: 1240px;
            padding-top: 1.45rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(8, 18, 29, 0.98), rgba(8, 18, 29, 0.96));
            border-right: 1px solid rgba(140, 170, 210, 0.12);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.25rem;
        }

        .pp-sidebar-shell {
            padding: 0.85rem 0.15rem 0.2rem 0.15rem;
        }

        .pp-sidebar-brand {
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 1.05rem 1rem;
            background: linear-gradient(180deg, rgba(16, 31, 50, 0.95), rgba(12, 24, 39, 0.92));
            box-shadow: var(--shadow);
            margin-bottom: 0.75rem;
        }

        .pp-sidebar-kicker {
            color: var(--primary);
            font-size: 0.73rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }

        .pp-sidebar-title {
            color: white;
            font-size: 1.12rem;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 0.32rem;
        }

        .pp-sidebar-copy {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .pp-sidebar-panel {
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 0.9rem 0.9rem 0.75rem 0.9rem;
            background: rgba(13, 24, 39, 0.82);
            margin-bottom: 0.75rem;
        }

        .pp-sidebar-panel h4 {
            margin: 0 0 0.45rem 0;
            color: white;
            font-size: 0.95rem;
            font-weight: 700;
        }

        .pp-sidebar-list {
            margin: 0;
            padding-left: 1rem;
            color: var(--muted);
            line-height: 1.65;
            font-size: 0.89rem;
        }

        .pp-hero {
            position: relative;
            overflow: hidden;
            border-radius: 28px;
            border: 1px solid var(--border);
            background:
                linear-gradient(135deg, rgba(11, 25, 40, 0.96), rgba(9, 20, 32, 0.92)),
                radial-gradient(circle at 15% 10%, rgba(92, 163, 255, 0.16), transparent 24%);
            box-shadow: var(--shadow);
            padding: 1.75rem 1.8rem 1.6rem 1.8rem;
            margin-bottom: 0.95rem;
        }

        .pp-hero::after {
            content: "";
            position: absolute;
            inset: auto -5% -30% auto;
            width: 260px;
            height: 260px;
            background: radial-gradient(circle, rgba(90, 165, 255, 0.14), transparent 60%);
            pointer-events: none;
        }

        .pp-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            color: var(--primary);
            font-size: 0.79rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .pp-title {
            color: white;
            font-size: 2.2rem;
            line-height: 1.06;
            font-weight: 850;
            max-width: 760px;
            margin: 0.6rem 0 0.75rem 0;
        }

        .pp-subtitle {
            color: var(--muted);
            font-size: 1rem;
            max-width: 720px;
            line-height: 1.68;
        }

        .pp-chip-row {
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
            margin-top: 0.95rem;
        }

        .pp-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.48rem 0.82rem;
            border-radius: 999px;
            border: 1px solid rgba(125, 177, 255, 0.22);
            background: rgba(16, 34, 56, 0.72);
            color: #d7e8ff;
            font-size: 0.84rem;
            font-weight: 600;
        }

        .pp-step-card,
        .pp-section-card,
        .pp-result-card,
        .pp-stat-card {
            border: 1px solid var(--border);
            border-radius: 24px;
            background: var(--surface);
            box-shadow: var(--shadow);
        }

        .pp-step-card {
            padding: 0.9rem 1rem;
            min-height: 100%;
        }

        .pp-step-index {
            color: var(--primary);
            font-size: 0.76rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .pp-step-title {
            color: white;
            font-size: 1rem;
            font-weight: 720;
            margin-bottom: 0.28rem;
        }

        .pp-step-copy {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .pp-section-card {
            padding: 1rem 1rem 0.85rem 1rem;
            height: 100%;
        }

        .pp-section-title {
            color: white;
            font-size: 1.1rem;
            font-weight: 720;
            margin-bottom: 0.15rem;
        }

        .pp-section-subtitle {
            color: var(--muted);
            font-size: 0.93rem;
            margin-bottom: 0.95rem;
            line-height: 1.6;
        }

        .pp-inline-card {
            border: 1px solid var(--border);
            border-radius: 20px;
            background: rgba(16, 31, 49, 0.75);
            padding: 0.85rem 0.95rem;
            margin-bottom: 0.7rem;
        }

        .pp-inline-card-title {
            color: white;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .pp-inline-card-copy {
            color: var(--muted);
            line-height: 1.65;
            font-size: 0.93rem;
        }

        .pp-stat-card {
            padding: 1rem;
        }

        .pp-stat-label {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.76rem;
            margin-bottom: 0.32rem;
        }

        .pp-stat-value {
            color: white;
            font-size: 1.75rem;
            font-weight: 820;
            line-height: 1.08;
        }

        .pp-note {
            border: 1px solid var(--border);
            border-left: 4px solid var(--primary);
            border-radius: 18px;
            background: rgba(17, 35, 56, 0.78);
            padding: 0.85rem 0.95rem;
            margin: 0.65rem 0;
        }

        .pp-note-title {
            color: white;
            font-weight: 700;
            margin-bottom: 0.22rem;
        }

        .pp-note-copy {
            color: var(--muted);
            line-height: 1.65;
            font-size: 0.93rem;
        }

        .pp-note-warning { border-left-color: var(--warning); }
        .pp-note-danger { border-left-color: var(--danger); }
        .pp-note-success { border-left-color: var(--accent); }

        .pp-bullet-list {
            margin: 0.1rem 0 0 0;
            padding-left: 1.1rem;
            color: var(--muted);
            line-height: 1.7;
        }

        .pp-takeaway-card {
            border: 1px solid var(--border);
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(15, 30, 48, 0.88), rgba(12, 23, 38, 0.88));
            padding: 1rem 1.05rem;
            box-shadow: var(--shadow);
        }

        .pp-takeaway-label {
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.74rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .pp-takeaway-text {
            color: white;
            font-size: 1rem;
            line-height: 1.7;
            font-weight: 560;
        }

        .pp-concern-meta {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.4rem;
            margin-bottom: 0.65rem;
        }

        .pp-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.32rem 0.68rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            border: 1px solid transparent;
        }

        .pp-badge-primary { background: rgba(94, 175, 255, 0.14); color: #cde4ff; border-color: rgba(94, 175, 255, 0.18); }
        .pp-badge-success { background: rgba(123, 240, 197, 0.13); color: #b7f8df; border-color: rgba(123, 240, 197, 0.18); }
        .pp-badge-warning { background: rgba(243, 191, 98, 0.12); color: #ffd996; border-color: rgba(243, 191, 98, 0.18); }
        .pp-badge-danger { background: rgba(255, 143, 168, 0.12); color: #ffc4d1; border-color: rgba(255, 143, 168, 0.18); }

        .pp-result-card {
            padding: 0.95rem 1rem;
            margin-bottom: 0.75rem;
        }

        .pp-quote {
            border-left: 3px solid rgba(126, 177, 255, 0.32);
            padding-left: 0.85rem;
            color: #dce8f8;
            margin: 0.55rem 0;
            line-height: 1.68;
        }

        .pp-memo {
            border: 1px solid var(--border);
            border-radius: 26px;
            background: linear-gradient(180deg, rgba(12, 26, 42, 0.92), rgba(10, 21, 34, 0.92));
            padding: 1.3rem 1.25rem;
            box-shadow: var(--shadow);
        }

        .pp-memo-body {
            color: #edf4ff;
            line-height: 1.85;
            font-size: 0.97rem;
        }

        .pp-footer-note {
            margin-top: 0.85rem;
            color: var(--muted);
            line-height: 1.7;
            font-size: 0.9rem;
        }

        .pp-results-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin: 0.35rem 0 0.95rem 0;
        }

        div[data-testid="stFileUploader"] {
            background: rgba(15, 30, 48, 0.78);
            border: 1px solid rgba(126, 177, 255, 0.16);
            border-radius: 20px;
            padding: 0.55rem;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
            background: rgba(8, 19, 30, 0.88);
            color: white;
            border: 1px solid rgba(126, 177, 255, 0.16);
            border-radius: 18px;
        }

        div[data-testid="stTextArea"] textarea::placeholder,
        div[data-testid="stTextInput"] input::placeholder {
            color: #7f97b5;
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            border-radius: 16px;
            border: 1px solid rgba(115, 167, 255, 0.18);
            background: linear-gradient(180deg, rgba(25, 54, 90, 0.96), rgba(20, 45, 74, 0.96));
            color: white;
            font-weight: 650;
            min-height: 46px;
            transition: all 0.18s ease;
            box-shadow: 0 12px 25px rgba(6, 16, 28, 0.18);
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            border-color: rgba(115, 167, 255, 0.34);
            transform: translateY(-1px);
            box-shadow: 0 14px 28px rgba(6, 16, 28, 0.24);
        }

        div[data-testid="stTabs"] button {
            color: #d4e3f6;
            font-weight: 650;
            border-radius: 14px 14px 0 0;
        }

        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: white;
        }

        [data-testid="stStatusWidget"] {
            border-radius: 18px;
            border: 1px solid var(--border);
            background: rgba(14, 26, 42, 0.82);
        }

        [data-testid="stExpander"] {
            border: 1px solid rgba(140, 170, 210, 0.14);
            border-radius: 18px;
            background: rgba(12, 24, 39, 0.62);
        }

        @media (max-width: 980px) {
            .pp-title { font-size: 1.9rem; }
            .pp-hero { padding: 1.4rem; }
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
        "demo_policy": demo_policy,
        "demo_comments": demo_comments,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_notice(title: str, body: str, tone: str = "primary") -> None:
    tone_class = {
        "primary": "",
        "warning": " pp-note-warning",
        "danger": " pp-note-danger",
        "success": " pp-note-success",
    }.get(tone, "")
    st.markdown(
        f"""
        <div class="pp-note{tone_class}">
            <div class="pp-note-title">{title}</div>
            <div class="pp-note-copy">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_badge(text: str, tone: str = "primary") -> str:
    return f'<span class="pp-badge pp-badge-{tone}">{text}</span>'


def render_sidebar() -> None:
    st.sidebar.markdown('<div class="pp-sidebar-shell">', unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div class="pp-sidebar-brand">
            <div class="pp-sidebar-kicker">PolicyPulse AI</div>
            <div class="pp-sidebar-title">Upload a policy. Add real feedback. Get a clearer next step.</div>
            <div class="pp-sidebar-copy">
                A clean workspace for turning policy drafts and public comments into a summary your team can actually use.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Load sample scenario", use_container_width=True):
        st.session_state["policy_text"] = st.session_state["demo_policy"]
        st.session_state["comments_text"] = st.session_state["demo_comments"]
        st.toast("Sample scenario is ready to review.", icon="🗂️")

    st.sidebar.markdown(
        """
        <div class="pp-sidebar-panel">
            <h4>How to use it</h4>
            <ul class="pp-sidebar-list">
                <li>Add a policy draft</li>
                <li>Add comments or import responses</li>
                <li>Run analysis and review the summary first</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.caption(
        "Built as a public showcase. If live provider limits are busy, retry after a short pause."
    )
    st.sidebar.markdown("</div>", unsafe_allow_html=True)


def read_policy_input(uploaded_file, pasted_text: str) -> str:
    if uploaded_file is not None:
        return parse_policy_file(uploaded_file)
    return pasted_text.strip()


def read_comments_input(uploaded_file, pasted_text: str) -> list[str]:
    if uploaded_file is not None:
        return parse_comments_file(uploaded_file)
    return parse_comments_text(pasted_text)


def resolve_comment_column(df: pd.DataFrame) -> str:
    preferred = {"comment", "comments", "feedback", "response", "responses", "student_comment"}
    for column in df.columns:
        if str(column).lower().strip() in preferred:
            return column
    return df.columns[0]


def parse_google_form_csv(csv_text: str) -> tuple[list[str], str]:
    if not csv_text or not csv_text.strip():
        raise ValueError("The connected Google Form returned an empty response sheet.")

    df = pd.read_csv(io.StringIO(csv_text))
    if df.empty or len(df.columns) == 0:
        raise ValueError("The Google Form response sheet is empty right now.")

    source_col = resolve_comment_column(df)
    comments = df[source_col].dropna().astype(str).str.strip()
    comments = [item for item in comments.tolist() if item]

    if not comments:
        raise ValueError("Responses were found, but none of the rows contained usable comment text yet.")

    return comments, source_col


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


def run_analysis_workflow(policy_text: str, comments: list[str]) -> dict:
    with st.status("Running the multi-agent review", expanded=True) as status:
        status.write("Extracting the core policy rules and affected groups.")
        status.write("Summarizing public sentiment and emotional tone.")
        status.write("Clustering repeated concerns and urgency patterns.")
        status.write("Comparing public concerns against the draft policy.")
        status.write("Preparing recommendations, memo, and survey blueprint.")
        result = run_pipeline(policy_text, comments)
        status.update(label="Analysis complete", state="complete")
        return result


def run_survey_workflow(policy_text: str) -> dict:
    with st.status("Preparing the survey blueprint", expanded=True) as status:
        status.write("Reading the policy context.")
        status.write("Drafting practical consultation questions.")
        status.write("Structuring the survey for Google Forms setup.")
        result = run_survey_generation(policy_text)
        status.update(label="Survey blueprint ready", state="complete")
        return result


def render_stat(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="pp-stat-card">
            <div class="pp-stat-label">{label}</div>
            <div class="pp-stat-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_takeaway(result: dict) -> str:
    policy = result["policy_analysis"]
    sentiment = result["sentiment_analysis"]
    concerns = result["concern_analysis"].get("concern_clusters", [])
    top_concern = concerns[0].get("theme") if concerns else "several stakeholder concerns"
    mood = sentiment.get("overall_mood", "mixed").lower()
    title = policy.get("policy_title", "This policy")
    return (
        f"{title} is landing with {mood} feedback so far. "
        f"The strongest pressure point is {top_concern}. "
        f"Start with the summary below, then review gaps and recommendations if you need a deeper read."
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="pp-hero">
            <div class="pp-eyebrow">Policy review, without the clutter</div>
            <div class="pp-title">Upload a policy. Add real feedback. Get a clearer next step.</div>
            <div class="pp-subtitle">
                PolicyPulse AI helps teams review draft policies faster. It pulls out the core rules, surfaces the
                biggest concerns, and turns scattered comments into a sharper decision.
            </div>
            <div class="pp-chip-row">
                <span class="pp-chip">Policy summary</span>
                <span class="pp-chip">Public feedback analysis</span>
                <span class="pp-chip">Executive memo</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_input_workspace() -> tuple[object, str, object, str]:
    step1, step2, step3 = st.columns(3, gap="medium")
    with step1:
        st.markdown(
            """
            <div class="pp-step-card">
                <div class="pp-step-index">Step 1</div>
                <div class="pp-step-title">Add the policy</div>
                <div class="pp-step-copy">Upload a file or paste the draft you want reviewed.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with step2:
        st.markdown(
            """
            <div class="pp-step-card">
                <div class="pp-step-index">Step 2</div>
                <div class="pp-step-title">Add feedback</div>
                <div class="pp-step-copy">Use a CSV, plain text comments, or imported form responses.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with step3:
        st.markdown(
            """
            <div class="pp-step-card">
                <div class="pp-step-index">Step 3</div>
                <div class="pp-step-title">Run analysis</div>
                <div class="pp-step-copy">Start with the summary, then open the deeper tabs only when you need them.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            """
            <div class="pp-section-card">
                <div class="pp-section-title">Policy document</div>
                <div class="pp-section-subtitle">
                    Upload a PDF, DOCX, or TXT file, or paste the draft directly.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        policy_file = st.file_uploader("Upload policy", type=["pdf", "docx", "txt"], key="policy_upload")
        policy_text = st.text_area(
            "Policy text",
            value=st.session_state["policy_text"],
            height=320,
            placeholder="Paste the draft policy here...",
        )
        st.session_state["policy_text"] = policy_text

    with right:
        st.markdown(
            """
            <div class="pp-section-card">
                <div class="pp-section-title">Public or student feedback</div>
                <div class="pp-section-subtitle">
                    Upload comments, paste them line by line, or import them from Google Forms.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        comments_file = st.file_uploader("Upload comments", type=["csv", "txt"], key="comments_upload")
        comments_text = st.text_area(
            "Comments",
            value=st.session_state["comments_text"],
            height=320,
            placeholder="Paste one comment per line...",
        )
        st.session_state["comments_text"] = comments_text

    return policy_file, policy_text, comments_file, comments_text


def render_google_forms_section() -> None:
    with st.expander("Optional: import responses from Google Forms", expanded=False):
        st.markdown(
            """
            <div class="pp-inline-card-copy">
                If you have already collected feedback through a Google Form, paste the form ID below and pull those responses into the comment workspace.
            </div>
            """,
            unsafe_allow_html=True,
        )

        form_id = st.text_input(
            "Google Form ID",
            value=st.session_state["google_form_id"],
            placeholder="Paste the Google Form ID here",
        )
        st.session_state["google_form_id"] = form_id

        if st.button("Fetch Google Form responses", use_container_width=True):
            if not form_id.strip():
                render_notice(
                    "A quick fix before we continue",
                    "Please paste a Google Form ID first, then try the import again.",
                    "warning",
                )
                return

            with st.spinner("Fetching responses from Google Forms..."):
                fetched = fetch_form_responses(form_id.strip())

            if fetched.get("error"):
                render_notice(
                    "We couldn’t fetch Google Form responses this time",
                    fetched["error"],
                    "danger",
                )
                return

            try:
                comments, source_col = parse_google_form_csv(fetched.get("csv", ""))
            except Exception as exc:
                render_notice(
                    "The Google Form was reached, but the responses could not be prepared",
                    f"{exc} If your sheet uses a custom column layout, make sure one column contains the actual feedback text.",
                    "warning",
                )
                return

            st.session_state["comments_text"] = "\n".join(comments)
            render_notice(
                "Responses imported successfully",
                f"We loaded {len(comments)} responses from the “{source_col}” column and placed them into the comments workspace.",
                "success",
            )
            st.rerun()


def render_action_row(policy_file, comments_file) -> None:
    info_col, analyze_col = st.columns([1.35, 1], gap="medium")

    with info_col:
        render_notice(
            "Before you run it",
            "Start with the main analysis. The app already prepares the survey blueprint as part of that run, so you do not need to launch two separate workflows unless you want a survey on its own.",
            "warning",
        )

    with analyze_col:
        analyze_clicked = st.button("Analyze policy", type="primary", use_container_width=True)

    if analyze_clicked:
        try:
            policy_input = read_policy_input(policy_file, st.session_state["policy_text"])
            comment_input = read_comments_input(comments_file, st.session_state["comments_text"])

            if not policy_input:
                render_notice(
                    "We need a policy document first",
                    "Please upload or paste the policy draft before starting the analysis.",
                    "warning",
                )
            elif not comment_input:
                render_notice(
                    "We need stakeholder feedback too",
                    "Please upload comments, paste them line by line, or import them from Google Forms.",
                    "warning",
                )
            else:
                result = run_analysis_workflow(policy_input, comment_input)
                st.session_state["analysis_results"] = result
                st.session_state["survey_results"] = result.get("survey")
                render_notice(
                    "Analysis finished successfully",
                    "Your summary is ready below. Start there, then open the deeper sections only if you need them.",
                    "success",
                )
        except Exception as exc:
            message = str(exc)
            lower_message = message.lower()
            if "rate limit" in lower_message or "too large" in lower_message or "token" in lower_message:
                friendly = (
                    "The live AI provider hit a temporary limit while processing this request. "
                    "Try a shorter input, wait a moment, and run the analysis again."
                )
            elif "api key" in lower_message or "groq_api_key" in lower_message:
                friendly = (
                    "The analysis service is not fully configured right now. "
                    "Please add the Groq API key in Streamlit secrets and redeploy."
                )
            else:
                friendly = f"Something interrupted the analysis run: {message}"
            render_notice("The analysis could not finish just yet", friendly, "danger")

    with st.expander("Only need a survey blueprint?", expanded=False):
        st.markdown(
            "Use this only when you want consultation questions without running the full policy analysis."
        )
        survey_clicked = st.button("Generate survey blueprint only", use_container_width=True)
        if survey_clicked:
            try:
                policy_input = read_policy_input(policy_file, st.session_state["policy_text"])
                if not policy_input:
                    render_notice(
                        "We need a policy document first",
                        "Please upload or paste the policy draft before generating a survey blueprint.",
                        "warning",
                    )
                else:
                    survey = run_survey_workflow(policy_input)
                    st.session_state["survey_results"] = survey
                    render_notice(
                        "Survey blueprint ready",
                        "You can review the structure below and optionally deploy it to Google Forms.",
                        "success",
                    )
            except Exception as exc:
                render_notice(
                    "The survey blueprint could not be generated",
                    f"We hit an issue while preparing the survey flow: {exc}",
                    "danger",
                )


def render_overview(result: dict) -> None:
    policy = result["policy_analysis"]
    sentiment = result["sentiment_analysis"]
    concerns = result["concern_analysis"].get("concern_clusters", [])
    recommendations = result["recommendations"]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_stat("Comments analyzed", str(sum(item.get("count", 0) for item in concerns)))
    with m2:
        render_stat("Concern clusters", str(len(concerns)))
    with m3:
        critical_count = sum(
            1 for item in recommendations.get("recommendations", []) if item.get("priority", "").lower() == "critical"
        )
        render_stat("Critical actions", str(critical_count))
    with m4:
        render_stat("Overall mood", sentiment.get("overall_mood", "Unknown"))

    takeaway = build_takeaway(result)
    st.markdown(
        f"""
        <div class="pp-takeaway-card">
            <div class="pp-takeaway-label">Fast read</div>
            <div class="pp-takeaway-text">{takeaway}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns((1.15, 0.95), gap="large")
    with left:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=["Support", "Opposition", "Neutral"],
                    y=[
                        sentiment.get("support_percentage", 0),
                        sentiment.get("opposition_percentage", 0),
                        sentiment.get("neutral_percentage", 0),
                    ],
                    marker_color=["#7bf0c5", "#ff8fa8", "#63b4ff"],
                )
            ]
        )
        fig.update_layout(
            height=330,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#eff5ff",
            yaxis_title="Share of comments",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Key policy structure")
        st.markdown("**Main rules**")
        st.markdown("\n".join(f"- {item}" for item in policy.get("main_rules", [])) or "- No rules extracted")
        if policy.get("affected_groups"):
            st.markdown("**Affected groups**")
            st.markdown("\n".join(f"- {item}" for item in policy.get("affected_groups", [])))
        if policy.get("unclear_clauses"):
            st.markdown("**Unclear clauses**")
            st.markdown("\n".join(f"- {item}" for item in policy.get("unclear_clauses", [])))


def render_concerns(result: dict) -> None:
    concerns = result["concern_analysis"].get("concern_clusters", [])
    if not concerns:
        st.info("No concern clusters are available yet.")
        return

    for concern in concerns:
        urgency = concern.get("urgency_level", "Medium").lower()
        tone = "danger" if urgency == "high" else "warning" if urgency == "medium" else "success"
        st.markdown(
            f"""
            <div class="pp-result-card">
                <div class="pp-section-title">{concern.get('theme', 'Concern cluster')}</div>
                <div class="pp-concern-meta">
                    {render_badge(f"{concern.get('count', 0)} comments", 'primary')}
                    {render_badge(f"{concern.get('urgency_level', 'Medium')} urgency", tone)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if concern.get("sample_comments"):
            st.markdown("**Representative feedback**")
            for sample in concern.get("sample_comments", [])[:3]:
                st.markdown(f'<div class="pp-quote">{sample}</div>', unsafe_allow_html=True)


def render_gaps(result: dict) -> None:
    gaps = result["gap_analysis"].get("gaps", [])
    if not gaps:
        st.info("No policy gaps are available yet.")
        return

    for gap in gaps:
        covered = bool(gap.get("covered_in_policy"))
        tone = "success" if covered else "danger"
        label = "Covered in policy" if covered else "Missing or unclear"
        st.markdown(
            f"""
            <div class="pp-result-card">
                <div class="pp-section-title">{gap.get('concern', 'Policy gap')}</div>
                <div class="pp-concern-meta">{render_badge(label, tone)}</div>
                <div class="pp-inline-card-copy">{gap.get('gap_description', '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_recommendations(result: dict) -> None:
    recommendations = result["recommendations"]
    items = recommendations.get("recommendations", [])
    top_three = items[:3]
    remaining = items[3:]

    st.markdown("### Top recommended actions")
    if top_three:
        for item in top_three:
            priority = item.get("priority", "Important")
            tone = {"Critical": "danger", "Important": "warning", "Nice-to-have": "primary"}.get(priority, "primary")
            st.markdown(
                f"""
                <div class="pp-result-card">
                    <div class="pp-inline-card-title">{item.get('action', '')}</div>
                    <div style="margin-top:0.35rem;">{render_badge(priority, tone)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No recommendations are available yet.")

    if remaining:
        with st.expander("See the full recommendation set", expanded=False):
            for item in remaining:
                priority = item.get("priority", "Important")
                tone = {"Critical": "danger", "Important": "warning", "Nice-to-have": "primary"}.get(priority, "primary")
                st.markdown(
                    f"""
                    <div class="pp-result-card">
                        <div class="pp-inline-card-title">{item.get('action', '')}</div>
                        <div style="margin-top:0.35rem;">{render_badge(priority, tone)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    revised = recommendations.get("revised_policy_suggestions", [])
    questions = recommendations.get("meeting_questions", [])
    if revised:
        with st.expander("Suggested wording updates", expanded=False):
            for item in revised:
                st.markdown(f"- {item}")
    if questions:
        with st.expander("Stakeholder meeting questions", expanded=False):
            for item in questions:
                st.markdown(f"- {item}")


def render_memo(result: dict) -> None:
    memo = result["recommendations"].get("executive_memo", "Executive memo not available.")
    st.markdown(
        f"""
        <div class="pp-memo">
            <div class="pp-section-title">Executive memo</div>
            <div class="pp-section-subtitle">
                The shortest leadership-ready read in the app.
            </div>
            <div class="pp-memo-body">{memo.replace(chr(10), '<br><br>')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pp-footer-note">This public build is optimized as a working showcase. During heavier usage, live AI provider quotas may occasionally delay or interrupt a run. When that happens, retrying after a short pause usually resolves it.</div>',
        unsafe_allow_html=True,
    )


def render_survey(result: dict) -> None:
    survey = result if "sections" in result else result.get("survey", {})
    if not survey:
        st.info("No survey blueprint is available yet.")
        return

    st.markdown(
        f"""
        <div class="pp-result-card">
            <div class="pp-section-title">{survey.get('title', 'Survey blueprint')}</div>
            <div class="pp-section-subtitle">{survey.get('description', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for section in survey.get("sections", []):
        st.markdown(f"### {section.get('section_name', 'Section')}")
        for question in section.get("questions", []):
            question_type = question.get("type", "text").replace("_", " ").title()
            st.markdown(
                f"""
                <div class="pp-result-card">
                    <div class="pp-inline-card-title">{question.get('question', '')}</div>
                    <div style="margin:0.35rem 0 0.65rem 0;">{render_badge(question_type, 'primary')}</div>
                """,
                unsafe_allow_html=True,
            )
            options = question.get("options", [])
            if options:
                st.markdown("**Options**")
                for option in options:
                    st.markdown(f"- {option}")
            st.markdown("</div>", unsafe_allow_html=True)

    steps = survey.get("google_forms_steps", [])
    if steps:
        st.markdown("### Manual Google Forms setup")
        for step in steps:
            st.markdown(f"- {step}")

    if st.button("Deploy survey to Google Forms", use_container_width=True):
        with st.spinner("Creating the Google Form..."):
            deployment = deploy_google_form(survey)

        if deployment.get("error"):
            render_notice(
                "We couldn’t create the Google Form just yet",
                deployment["error"],
                "danger",
            )
        else:
            render_notice(
                "Google Form created successfully",
                "Your survey has been prepared and the live form links are ready below.",
                "success",
            )
            st.markdown(f"- **Live form:** {deployment.get('url')}")
            if deployment.get("edit_url"):
                st.markdown(f"- **Edit form:** {deployment.get('edit_url')}")
            if deployment.get("form_id"):
                st.session_state["google_form_id"] = deployment["form_id"]


def render_results(result: dict, survey_result: dict | None) -> None:
    st.markdown("---")
    st.markdown("## Analysis summary")
    report_md = build_markdown_report(result)
    toolbar_left, toolbar_right = st.columns([1.4, 1], gap="medium")
    with toolbar_left:
        st.markdown(
            "Start with the overview tab. The rest is there when you want more detail, not all at once."
        )
    with toolbar_right:
        st.download_button(
            "Download Markdown report",
            data=report_md,
            file_name="policypulse-report.md",
            mime="text/markdown",
            use_container_width=True,
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
        render_survey(survey_result or result)


def main() -> None:
    inject_styles()
    init_state()
    render_sidebar()
    render_hero()

    if not get_secret("GROQ_API_KEY"):
        render_notice(
            "Live analysis is not configured yet",
            "Add GROQ_API_KEY in your Streamlit secrets before running real analysis on the deployed app.",
            "warning",
        )

    policy_file, _, comments_file, _ = render_input_workspace()
    render_google_forms_section()
    render_action_row(policy_file, comments_file)

    result = st.session_state.get("analysis_results")
    survey_result = st.session_state.get("survey_results")

    if result is None and survey_result is None:
        render_notice(
            "Ready when you are",
            "Load the sample scenario from the sidebar or upload your own policy and comments to start a live review.",
            "primary",
        )
        return

    if result is not None:
        render_results(result, survey_result)
    elif survey_result is not None:
        st.markdown("---")
        render_survey(survey_result)


if __name__ == "__main__":
    main()
