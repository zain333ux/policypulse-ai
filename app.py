import streamlit as st
import pandas as pd
import json
import io
import plotly.graph_objects as go
import plotly.express as px
import textwrap

from src.agents.pipeline import run_pipeline, run_survey_generation
from src.agents.policy_extraction_agent import extract_policy_details
from src.agents.sentiment_agent import analyze_sentiment
from src.agents.concern_clustering_agent import cluster_concerns
from src.agents.gap_detection_agent import detect_gaps
from src.agents.recommendation_agent import generate_recommendations
import src.agents.survey_generator_agent as survey_agent
import importlib
import src.parsers.file_parser
import src.parsers.comment_parser

importlib.reload(src.parsers.file_parser)
importlib.reload(src.parsers.comment_parser)

from src.parsers.file_parser import parse_policy_file
from src.parsers.comment_parser import parse_comments_file, parse_comments_text
import re

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def sanitize_html(text: str) -> str:
    if not isinstance(text, str):
        return text
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = clean_text.replace("&nbsp;", " ")
    clean_text = clean_text.replace("&amp;", "&")
    clean_text = clean_text.replace("&lt;", "<")
    clean_text = clean_text.replace("&gt;", ">")
    clean_text = clean_text.replace("&quot;", '"')
    return clean_text

def get_status_markdown(covered: bool) -> str:
    return ":green[● Covered]" if covered else ":red[● Omission]"

def get_severity_markdown(severity: str) -> str:
    severity_clean = sanitize_html(severity).strip().upper()
    if not severity_clean:
        return ""
    if any(x in severity_clean.lower() for x in ['critical', 'high']):
        return f":red[● {severity_clean} SEVERITY]"
    elif 'medium' in severity_clean.lower():
        return f":orange[● {severity_clean} SEVERITY]"
    elif 'low' in severity_clean.lower():
        return f":blue[● {severity_clean} SEVERITY]"
    else:
        return f":violet[● {severity_clean}]"

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="PolicyPulse AI — Civic Intelligence Dashboard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load background image dynamically
import base64
import os

bg_base64 = ""
bg_ext = "png"
bg_path = "assets/background.png"
if not os.path.exists(bg_path):
    bg_path = "assets/background.jpg"
    bg_ext = "jpeg"

if os.path.exists(bg_path):
    try:
        with open(bg_path, "rb") as image_file:
            bg_base64 = base64.b64encode(image_file.read()).decode()
    except Exception:
        pass

if bg_base64:
    bg_style = f"""
    .stApp {{
        background-image: linear-gradient(rgba(11, 18, 32, 0.92), rgba(11, 18, 32, 0.92)), url(data:image/{bg_ext};base64,{bg_base64});
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: #E8EDF5;
        font-family: 'Inter', sans-serif;
        overflow-x: hidden !important;
    }}
    """
else:
    bg_style = """
    .stApp {
        background-color: #0B1220;
        color: #E8EDF5;
        font-family: 'Inter', sans-serif;
        overflow-x: hidden !important;
    }
    """

st.markdown(f"<style>{bg_style}</style>", unsafe_allow_html=True)

# ==========================================
# DESIGN SYSTEM CSS (Figma Tokens)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

    /* ─── Layout ─── */
    .block-container {
        max-width: 1200px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }

    /* ─── Sidebar ─── */
    section[data-testid="stSidebar"] {
        background-color: #0D1626 !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #0D1626 !important;
    }

    /* ─── Hero Title ─── */
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #E8EDF5;
        margin-bottom: 2px;
    }
    .hero-subtitle {
        font-size: 0.8rem;
        color: #4A6080;
        margin-bottom: 16px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ─── Section Headers ─── */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: #E8EDF5;
        margin-bottom: 3px;
    }
    .section-sub {
        font-size: 0.72rem;
        color: #4A6080;
        margin-bottom: 12px;
    }

    /* ─── Badges ─── */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .badge-teal { background: rgba(45,212,191,0.10); color: #2DD4BF; border: 1px solid rgba(45,212,191,0.20); }
    .badge-blue { background: rgba(59,130,246,0.10); color: #93C5FD; border: 1px solid rgba(59,130,246,0.20); }
    .badge-violet { background: rgba(139,92,246,0.10); color: #C4B5FD; border: 1px solid rgba(139,92,246,0.20); }
    .badge-coral { background: rgba(239,68,68,0.10); color: #EF4444; border: 1px solid rgba(239,68,68,0.20); }
    .badge-amber { background: rgba(245,158,11,0.10); color: #F59E0B; border: 1px solid rgba(245,158,11,0.20); }

    /* ─── Cards (Glassmorphic) ─── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #111827 !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
        box-shadow: none !important;
        margin-bottom: 1rem !important;
    }

    /* ─── KPI Cards ─── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 1.25rem;
    }
    .kpi-card {
        background: #111827;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 18px 20px;
    }
    .kpi-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .kpi-label {
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #6B7FA3;
        font-family: 'JetBrains Mono', monospace;
    }
    .kpi-icon {
        width: 28px;
        height: 28px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
    }
    .kpi-value {
        font-size: 1.9rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: #E8EDF5;
        line-height: 1;
        margin-bottom: 6px;
    }
    .kpi-delta {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 10.5px;
        font-family: 'JetBrains Mono', monospace;
    }
    .kpi-delta-sub {
        color: #4A6080;
        font-size: 10.5px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ─── Pipeline Stepper (Horizontal) ─── */
    .h-pipeline {
        display: flex;
        align-items: stretch;
        gap: 0;
        margin-bottom: 1.25rem;
    }
    .h-pipeline-step {
        flex: 1;
        display: flex;
        align-items: center;
    }
    .h-pipeline-card {
        flex: 1;
        border-radius: 10px;
        padding: 14px 12px;
        min-height: 100px;
    }
    .h-pipeline-card.complete {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .h-pipeline-card.active {
        background: rgba(45,212,191,0.06);
        border: 1px solid rgba(45,212,191,0.25);
    }
    .h-pipeline-card.queued {
        background: rgba(255,255,255,0.01);
        border: 1px solid rgba(255,255,255,0.04);
    }
    .h-pipeline-icon {
        width: 24px;
        height: 24px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        margin-right: 6px;
        vertical-align: middle;
    }
    .h-pipeline-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
        vertical-align: middle;
        margin-left: 4px;
    }
    .h-pipeline-name {
        font-size: 11.5px;
        font-weight: 600;
        margin-top: 6px;
    }
    .h-pipeline-desc {
        font-size: 9.5px;
        color: #3D5070;
        margin-top: 2px;
        line-height: 1.3;
    }
    .h-pipeline-badge {
        display: inline-block;
        font-size: 8px;
        padding: 2px 6px;
        border-radius: 3px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        margin-top: 8px;
    }
    .h-pipeline-arrow {
        display: flex;
        align-items: center;
        padding: 0 4px;
        flex-shrink: 0;
        font-size: 14px;
    }

    /* ─── Sidebar Pipeline (vertical) ─── */
    .pipeline-container { margin-top: 10px; margin-bottom: 10px; }
    .pipeline-step {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 10px;
        border-radius: 8px;
        margin-bottom: 5px;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.04);
    }
    .pipeline-step.active { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.20); }
    .pipeline-step.done { background: rgba(45,212,191,0.06); border-color: rgba(45,212,191,0.15); }
    .step-number {
        display: flex; align-items: center; justify-content: center;
        width: 20px; height: 20px; border-radius: 50%;
        font-size: 9px; font-weight: 700; font-family: 'JetBrains Mono', monospace;
        background: #111827; border: 1px solid rgba(255,255,255,0.08); flex-shrink: 0;
    }
    .pipeline-step.active .step-number { background: #F59E0B; color: #0B1220; border-color: #F59E0B; }
    .pipeline-step.done .step-number { background: #2DD4BF; color: #0B1220; border-color: #2DD4BF; }
    .step-name { font-size: 11.5px; font-weight: 600; color: #E8EDF5; }
    .step-desc { font-size: 9.5px; color: #4A6080; margin-top: 1px; }

    /* ─── Buttons ─── */
    .stButton>button {
        background: #2DD4BF !important;
        color: #0B1220 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        transition: all 0.15s ease !important;
    }
    .stButton>button:hover {
        filter: brightness(1.08) !important;
        transform: translateY(-1px) !important;
    }
    .stButton>button:active {
        transform: translateY(0) scale(0.98) !important;
    }
    .stButton>button[data-testid="stBaseButton-secondary"] {
        background: #162032 !important;
        color: #A0AEC0 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    .stButton>button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(255,255,255,0.05) !important;
        border-color: #2DD4BF !important;
        color: #E8EDF5 !important;
    }

    /* ─── Inputs ─── */
    .stTextArea textarea {
        background-color: rgba(255,255,255,0.04) !important;
        color: #E8EDF5 !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextArea textarea:focus {
        border-color: #2DD4BF !important;
        box-shadow: 0 0 0 1px #2DD4BF !important;
    }
    [data-testid="stFileUploader"] {
        background-color: rgba(255,255,255,0.03) !important;
        border: 1px dashed rgba(255,255,255,0.10) !important;
        border-radius: 10px !important;
        padding: 8px !important;
    }

    /* ─── Evidence Quotes ─── */
    .evidence-quote {
        font-size: 13px;
        line-height: 1.55;
        color: #A0AEC0;
        font-style: italic;
        background: #0D1626;
        border-left: 3px solid #2DD4BF;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 0 8px 8px 0;
    }

    /* ─── Feedback Card ─── */
    .feedback-card {
        background: #0D1626;
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .feedback-avatar {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: 700;
        background: #1E3A5F;
        color: #93C5FD;
        flex-shrink: 0;
        margin-right: 8px;
        vertical-align: middle;
    }
    .feedback-author {
        font-size: 12px;
        font-weight: 600;
        color: #E8EDF5;
    }
    .feedback-role {
        font-size: 10px;
        color: #4A6080;
        margin-left: 6px;
    }
    .feedback-text {
        font-size: 12.5px;
        color: #A0AEC0;
        line-height: 1.5;
        margin-top: 8px;
    }
    .feedback-tag {
        display: inline-block;
        font-size: 9px;
        padding: 2px 7px;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        background: #162032;
        color: #6B7FA3;
        margin-right: 4px;
        margin-top: 8px;
    }

    /* ─── Executive Memo ─── */
    .memo-container {
        background: #0D1626 !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 12px !important;
        padding: 2.5rem !important;
        font-family: 'Inter', sans-serif !important;
        color: #A0AEC0 !important;
        line-height: 1.75 !important;
    }
    .memo-letterhead {
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding-bottom: 1rem;
        margin-bottom: 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }
    .memo-org {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #2DD4BF;
        font-weight: 600;
    }
    .memo-date {
        font-size: 10px;
        color: #4A6080;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ─── Tables ─── */
    table { width: 100%; border-collapse: collapse; color: #E8EDF5; }
    th {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px; text-transform: uppercase; color: #4A6080;
        letter-spacing: 0.06em;
        border-bottom: 1px solid rgba(255,255,255,0.07) !important;
        padding: 8px 10px !important;
        text-align: left;
    }
    td {
        padding: 10px !important;
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
        font-size: 12.5px;
    }
    tr:hover td { background-color: rgba(255,255,255,0.02) !important; }

    /* ─── Tabs ─── */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        border: 1px solid rgba(255,255,255,0.06);
        background-color: rgba(255,255,255,0.02);
        border-radius: 8px 8px 0 0;
        padding: 8px 14px;
        color: #6B7FA3;
        font-weight: 500;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #111827;
        color: #E8EDF5 !important;
        border-bottom: 2px solid #2DD4BF !important;
        border-color: rgba(255,255,255,0.08);
    }

    /* ─── Expanders ─── */
    .stMain .streamlit-expanderHeader {
        background-color: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 8px !important;
        color: #E8EDF5 !important;
    }
    .stMain .streamlit-expanderContent {
        background-color: rgba(255,255,255,0.01) !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* ─── Survey Question Cards ─── */
    .survey-q-card {
        background: #0D1626;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 10px;
    }
    .survey-q-num {
        font-size: 9px;
        font-family: 'JetBrains Mono', monospace;
        color: #2DD4BF;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .survey-q-text {
        font-size: 13.5px;
        font-weight: 500;
        color: #E8EDF5;
        line-height: 1.45;
        margin-bottom: 8px;
    }
    .survey-q-type {
        display: inline-block;
        font-size: 9px;
        padding: 2px 7px;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .survey-q-option {
        font-size: 12px;
        color: #6B7FA3;
        padding: 4px 0 4px 14px;
        border-left: 2px solid rgba(255,255,255,0.06);
        margin-bottom: 2px;
    }

    /* Hide default Streamlit header & footer */
    header[data-testid="stHeader"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# STATE MANAGEMENT
# ==========================================
if 'analysis_results' not in st.session_state:
    st.session_state['analysis_results'] = None
if 'survey_results' not in st.session_state:
    st.session_state['survey_results'] = None
if 'demo_policy' not in st.session_state:
    st.session_state['demo_policy'] = ""
if 'demo_comments' not in st.session_state:
    st.session_state['demo_comments'] = ""

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    # Logo
    st.markdown(
        '<div style="display:flex; align-items:center; gap:10px; padding: 4px 0 12px 0;">'
        '<div style="width:28px; height:28px; border-radius:6px; display:flex; align-items:center; justify-content:center;'
        ' background: linear-gradient(135deg, #2DD4BF, #3B82F6); font-size:14px;">🌐</div>'
        '<div>'
        '<div style="font-family:\'Space Grotesk\', sans-serif; font-size:15px; font-weight:700; color:#E8EDF5;">PolicyPulse AI</div>'
        '<div style="font-size:9px; text-transform:uppercase; color:#4A6080; letter-spacing:0.10em;'
        ' font-family:\'JetBrains Mono\', monospace;">Civic Intelligence System</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Live indicator
    st.markdown(
        '<div style="display:flex; align-items:center; gap:7px; padding:8px 0; border-top:1px solid rgba(255,255,255,0.06); border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:12px;">'
        '<span style="position:relative; display:inline-flex; width:8px; height:8px;">'
        '<span style="position:absolute; display:inline-flex; width:100%; height:100%; border-radius:50%; background:#2DD4BF; opacity:0.6; animation:ping 1.5s infinite;"></span>'
        '<span style="position:relative; display:inline-flex; width:8px; height:8px; border-radius:50%; background:#2DD4BF;"></span>'
        '</span>'
        '<span style="font-size:10px; color:#2DD4BF; font-family:\'JetBrains Mono\', monospace; font-weight:500;">Live Analysis Engine</span>'
        '</div>'
        '<style>@keyframes ping{0%{transform:scale(1);opacity:0.7}75%,100%{transform:scale(2.2);opacity:0}}</style>',
        unsafe_allow_html=True
    )

    # API Key Check
    api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    if not api_key_configured:
        st.error("⚠️ **OpenAI API Key Missing**\n\nAdd `OPENAI_API_KEY` to your `.env` file.")

    # Agent Pipeline Status
    st.markdown('<div style="font-size:9px; text-transform:uppercase; letter-spacing:0.08em; color:#3D5070; font-family:\'JetBrains Mono\', monospace; font-weight:600; margin-bottom:6px;">Agent Pipeline</div>', unsafe_allow_html=True)

    has_analysis = st.session_state['analysis_results'] is not None
    has_survey = st.session_state['survey_results'] is not None

    def draw_pipeline(statuses):
        steps = [
            ("01", "Policy Extraction", "Rules, penalties, unclear clauses", statuses.get("01", "Waiting")),
            ("02", "Sentiment Analysis", "Support, opposition, mood", statuses.get("02", "Waiting")),
            ("03", "Concern Clustering", "Theme grouping from feedback", statuses.get("03", "Waiting")),
            ("04", "Gap Detection", "Policy coverage audit", statuses.get("04", "Waiting")),
            ("05", "Recommendations", "Action synthesis & memo", statuses.get("05", "Waiting")),
            ("06", "Survey Generator", "Feedback instrument design", statuses.get("06", "Optional"))
        ]

        pipeline_html = "<div class='pipeline-container'>"
        for num, name, desc, status in steps:
            step_class = "pipeline-step done" if status == "Done" else "pipeline-step active" if status == "Running" else "pipeline-step"
            status_color = "#2DD4BF" if status == "Done" else "#F59E0B" if status == "Running" else "#6B7FA3"
            status_bg = "rgba(45,212,191,0.10)" if status == "Done" else "rgba(245,158,11,0.10)" if status == "Running" else "rgba(255,255,255,0.04)"
            pipeline_html += (
                f'<div class="{step_class}">'
                f'<div class="step-number">{num}</div>'
                '<div>'
                f'<div class="step-name">{name} '
                f'<span class="badge" style="font-size:7px; padding:1px 5px; background:{status_bg}; color:{status_color}; border:1px solid {status_color}33; margin-left:4px; vertical-align:middle;">{status}</span>'
                '</div>'
                f'<div class="step-desc">{desc}</div>'
                '</div></div>'
            )
        pipeline_html += "</div>"
        return pipeline_html

    pipeline_placeholder = st.sidebar.empty()

    initial_statuses = {
        "01": "Done" if has_analysis else "Waiting",
        "02": "Done" if has_analysis else "Waiting",
        "03": "Done" if has_analysis else "Waiting",
        "04": "Done" if has_analysis else "Waiting",
        "05": "Done" if has_analysis else "Waiting",
        "06": "Done" if has_survey else "Optional"
    }
    pipeline_placeholder.markdown(draw_pipeline(initial_statuses), unsafe_allow_html=True)

    # Separator + Demo Scenarios
    st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:12px 0; padding-top:12px;">'
                '<div style="font-size:9px; text-transform:uppercase; letter-spacing:0.08em; color:#3D5070; font-family:\'JetBrains Mono\', monospace; font-weight:600; margin-bottom:8px;">Demo Scenarios</div>'
                '</div>', unsafe_allow_html=True)

    if st.sidebar.button("🚀 Load Attendance Policy Scenario", use_container_width=True):
        try:
            with open("sample_data/attendance_policy.txt", "r", encoding="utf-8") as f:
                st.session_state['demo_policy'] = f.read()
            df_comments = pd.read_csv("sample_data/student_comments.csv")
            st.session_state['demo_comments'] = "\n".join(df_comments['comment'].dropna().astype(str).tolist())
            st.toast("Scenario Loaded!", icon="🚀")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Failed to load demo scenario: {e}")

    # System section footer
    st.markdown(
        '<div style="border-top:1px solid rgba(255,255,255,0.06); margin-top:16px; padding-top:14px;">'
        '<div style="display:flex; align-items:center; gap:8px;">'
        '<div style="width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center;'
        ' font-size:10px; font-weight:700; background:#1E3A5F; color:#93C5FD; flex-shrink:0;">PP</div>'
        '<div>'
        '<div style="font-size:11px; font-weight:600; color:#E8EDF5;">PolicyPulse</div>'
        '<div style="font-size:9px; color:#4A6080; font-family:\'JetBrains Mono\', monospace;">Hackathon MVP v1.0</div>'
        '</div></div></div>',
        unsafe_allow_html=True
    )

# ==========================================
# HEADER
# ==========================================
h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    st.markdown('<div class="hero-title">Civic Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">PolicyPulse AI — Multi-Agent Policy Analysis Engine</div>', unsafe_allow_html=True)
with h_col2:
    st.markdown(
        '<div style="text-align:right; padding-top: 8px;">'
        '<span class="badge badge-teal">Education</span>'
        '<span class="badge badge-blue" style="margin-left:4px;">Civic Tech</span>'
        '<span class="badge badge-violet" style="margin-left:4px;">Multi-Agent AI</span>'
        '</div>',
        unsafe_allow_html=True
    )

st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:8px 0 16px 0;"></div>', unsafe_allow_html=True)

# ==========================================
# INPUT AREA
# ==========================================
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("##### 📋 Draft Policy Document")
        st.caption("Upload a proposed policy (PDF, TXT, DOCX) or paste below.")
        policy_file = st.file_uploader("Upload Policy", type=["pdf", "txt", "docx"], label_visibility="collapsed")
        pasted_policy = st.text_area("Or Paste Policy Text",
                                     value=st.session_state['demo_policy'],
                                     height=160,
                                     placeholder="Paste text of the policy here...")

with col2:
    with st.container(border=True):
        st.markdown("##### 🗣️ Public / Stakeholder Comments")
        st.caption("Upload CSV (with 'comment' column) or paste one per line.")
        comments_file = st.file_uploader("Upload Comments", type=["csv", "txt"], label_visibility="collapsed")
        pasted_comments = st.text_area("Or Paste Comments (one per line)",
                                       value=st.session_state['demo_comments'],
                                       height=160,
                                       placeholder="I don't agree with the current rules...\nThis policy doesn't handle exemptions...")

# Run controls
ctrl1, ctrl2 = st.columns(2)
with ctrl1:
    analyze_btn = st.button("🔍 Analyze Public Feedback", type="primary", use_container_width=True)
with ctrl2:
    survey_btn = st.button("📋 Generate Feedback Survey Blueprint", use_container_width=True)

# ==========================================
# PROCESSING PIPELINE LOGIC
# ==========================================
def get_parsed_inputs():
    final_policy = ""
    final_comments = []
    policy_error = None
    comments_error = None

    if policy_file:
        try:
            final_policy = parse_policy_file(policy_file)
        except Exception as e:
            policy_error = f"Error reading policy file: {e}"
    elif pasted_policy.strip():
        final_policy = pasted_policy.strip()

    if comments_file:
        try:
            final_comments = parse_comments_file(comments_file)
        except Exception as e:
            comments_error = f"Error reading comments file: {e}"
    elif pasted_comments.strip():
        stripped_pasted = pasted_comments.strip()
        if stripped_pasted.startswith("id,comment") or stripped_pasted.startswith("comment") or "," in stripped_pasted.split('\n')[0]:
            try:
                df = pd.read_csv(io.StringIO(stripped_pasted))
                target_col = None
                possible_columns = ['comment', 'comments', 'feedback', 'text', 'review', 'reviews', 'response', 'responses', 'content', 'message', 'messages']
                normalized_cols = {col.lower().strip(): col for col in df.columns}
                for col_name in possible_columns:
                    if col_name in normalized_cols:
                        target_col = normalized_cols[col_name]
                        break
                if target_col is None and not df.empty:
                    string_cols = [c for c in df.columns if df[c].dtype == object]
                    if string_cols:
                        target_col = string_cols[0]
                    else:
                        target_col = df.columns[0]
                if target_col is not None:
                    final_comments = df[target_col].dropna().astype(str).tolist()
                    final_comments = [c.strip() for c in final_comments if c.strip()]
                else:
                    final_comments = parse_comments_text(pasted_comments)
            except Exception:
                final_comments = parse_comments_text(pasted_comments)
        else:
            final_comments = parse_comments_text(pasted_comments)

    if policy_error:
        st.error(policy_error)
    if comments_error:
        st.error(comments_error)
    if policy_error or comments_error:
        return "PARSING_ERROR", "PARSING_ERROR"

    return final_policy, final_comments

# Success notifications
notification_box = st.empty()
if st.session_state.get('show_analysis_success'):
    notification_box.success("✅ Analysis Complete — Policy Intelligence Generated")
if st.session_state.get('show_survey_success'):
    notification_box.success("✅ Survey blueprint compiled successfully!")

if analyze_btn:
    st.session_state['show_analysis_success'] = False
    st.session_state['show_survey_success'] = False
    notification_box.empty()

    has_policy_input = bool(policy_file or pasted_policy.strip())
    has_comments_input = bool(comments_file or pasted_comments.strip())

    if not has_policy_input:
        st.error("Please provide a draft policy document to continue.")
    elif not has_comments_input:
        st.error("Please provide public feedback comments to continue.")
    else:
        policy, comments = get_parsed_inputs()
        if policy == "PARSING_ERROR" or comments == "PARSING_ERROR":
            pass
        elif not policy:
            st.error("Please provide a draft policy document to continue.")
        elif not comments:
            st.error("Please provide public feedback comments to continue.")
        else:
            status_box = st.empty()

            current_statuses = {
                "01": "Waiting", "02": "Waiting", "03": "Waiting",
                "04": "Waiting", "05": "Waiting",
                "06": "Done" if has_survey else "Optional"
            }

            try:
                current_statuses["01"] = "Running"
                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)
                status_box.info("🤖 Agent 1: Extracting policy rules and unclear clauses...")
                policy_analysis = extract_policy_details(policy)
                current_statuses["01"] = "Done"

                current_statuses["02"] = "Running"
                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)
                status_box.info("🤖 Agent 2: Analyzing sentiment scores and overall mood...")
                sentiment_analysis = analyze_sentiment(comments)
                current_statuses["02"] = "Done"

                current_statuses["03"] = "Running"
                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)
                status_box.info("🤖 Agent 3: Clustering stakeholder comments into themes...")
                concern_analysis = cluster_concerns(comments)
                current_statuses["03"] = "Done"

                current_statuses["04"] = "Running"
                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)
                status_box.info("🤖 Agent 4: Comparing policy against public concerns...")
                gap_analysis = detect_gaps(policy_analysis, concern_analysis)
                current_statuses["04"] = "Done"

                current_statuses["05"] = "Running"
                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)
                status_box.info("🤖 Agent 5: Drafting actionable recommendations & memo...")
                recommendations = generate_recommendations(policy_analysis, gap_analysis)
                current_statuses["05"] = "Done"

                current_statuses["06"] = "Running"
                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)
                status_box.info("🤖 Agent 6: Designing survey questions & outreach blueprint...")
                survey = survey_agent.generate_survey(policy)
                current_statuses["06"] = "Done"

                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)

                st.session_state['analysis_results'] = {
                    "policy_analysis": policy_analysis,
                    "sentiment_analysis": sentiment_analysis,
                    "concern_analysis": concern_analysis,
                    "gap_analysis": gap_analysis,
                    "recommendations": recommendations,
                    "survey": survey
                }
                st.session_state['survey_results'] = survey
                st.session_state['show_analysis_success'] = True
                status_box.empty()
                st.rerun()
            except Exception as e:
                status_box.empty()
                st.error(f"Execution failed: {e}")

if survey_btn:
    st.session_state['show_analysis_success'] = False
    st.session_state['show_survey_success'] = False
    notification_box.empty()

    has_policy_input = bool(policy_file or pasted_policy.strip())

    if not has_policy_input:
        st.error("Please provide a draft policy document to generate a feedback survey blueprint.")
    else:
        policy, _ = get_parsed_inputs()
        if policy == "PARSING_ERROR":
            pass
        elif not policy:
            st.error("Please provide a draft policy document to generate a feedback survey blueprint.")
        else:
            status_box = st.empty()

            current_statuses = {
                "01": "Done" if has_analysis else "Waiting",
                "02": "Done" if has_analysis else "Waiting",
                "03": "Done" if has_analysis else "Waiting",
                "04": "Done" if has_analysis else "Waiting",
                "05": "Done" if has_analysis else "Waiting",
                "06": "Running"
            }

            try:
                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)
                status_box.info("🤖 Agent 6: Designing survey questions & outreach blueprint...")
                survey_data = run_survey_generation(policy)
                current_statuses["06"] = "Done"
                pipeline_placeholder.markdown(draw_pipeline(current_statuses), unsafe_allow_html=True)

                st.session_state['survey_results'] = survey_data
                st.session_state['show_survey_success'] = True
                status_box.empty()
                st.rerun()
            except Exception as e:
                status_box.empty()
                st.error(f"Survey Generation failed: {e}")

# ==========================================
# RESULTS VIEWPORT
# ==========================================
res = st.session_state.get('analysis_results')
surv = st.session_state.get('survey_results')

if res or surv:
    st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:20px 0;"></div>', unsafe_allow_html=True)

    # ─────── OVERVIEW METRICS + CHARTS ───────
    if res:
        sentiment = res.get('sentiment_analysis', {})
        policy_data = res.get('policy_analysis', {})
        gaps_data = res.get('gap_analysis', {})
        gaps_list = gaps_data.get('gaps', gaps_data.get('policy_gaps', []))

        support_pct = sentiment.get('support_percentage', sentiment.get('support', 0))
        opposition_pct = sentiment.get('opposition_percentage', sentiment.get('opposition', 0))
        neutral_pct = sentiment.get('neutral_percentage', sentiment.get('neutral', 0))
        mood = sentiment.get('overall_mood', sentiment.get('mood', 'Mixed'))

        num_rules = len(policy_data.get('main_rules', []))
        num_gaps = len(gaps_list)

        # KPI Row
        kpi_html = '<div class="kpi-grid">'
        kpis = [
            ("Public Support", f"{support_pct}%", "#2DD4BF", "📈"),
            ("Opposition", f"{opposition_pct}%", "#EF4444", "📉"),
            ("Neutral", f"{neutral_pct}%", "#6B7FA3", "➖"),
            ("Critical Gaps", f"{num_gaps}", "#F59E0B", "⚠️"),
        ]
        for label, value, color, icon in kpis:
            kpi_html += (
                f'<div class="kpi-card">'
                f'<div class="kpi-header">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-icon" style="background:{color}18;">{icon}</div>'
                f'</div>'
                f'<div class="kpi-value">{value}</div>'
                f'<div class="kpi-delta">'
                f'<span style="color:{color};">●</span>'
                f'<span class="kpi-delta-sub">Overall mood: {mood}</span>'
                f'</div>'
                f'</div>'
            )
        kpi_html += '</div>'
        st.markdown(kpi_html, unsafe_allow_html=True)

        # Charts Row
        chart_col1, chart_col2 = st.columns([2, 3])

        with chart_col1:
            with st.container(border=True):
                st.markdown('<div class="section-header">Sentiment Distribution</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="section-sub">Analyzed across stakeholder feedback</div>', unsafe_allow_html=True)

                labels = ['Support', 'Opposition', 'Neutral']
                values = [support_pct, opposition_pct, neutral_pct]
                colors = ['#2DD4BF', '#EF4444', '#6B7FA3']

                fig = go.Figure(data=[go.Pie(
                    labels=labels, values=values, hole=.48,
                    marker_colors=colors,
                    textinfo='percent',
                    textfont=dict(color='#0B1220', size=11, family='JetBrains Mono')
                )])
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#E8EDF5',
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5,
                                font=dict(size=10, family='JetBrains Mono', color='#6B7FA3')),
                    margin=dict(t=5, b=5, l=5, r=5), height=190
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with chart_col2:
            with st.container(border=True):
                st.markdown('<div class="section-header">Policy Gaps by Severity</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-sub">Identified coverage deficiencies</div>', unsafe_allow_html=True)

                if gaps_list:
                    # Build severity counts
                    severity_counts = {"High": 0, "Medium": 0, "Low": 0}
                    for g in gaps_list:
                        sev = sanitize_html(g.get('severity', 'Medium')).strip().lower()
                        if any(x in sev for x in ['critical', 'high']):
                            severity_counts["High"] += 1
                        elif 'low' in sev:
                            severity_counts["Low"] += 1
                        else:
                            severity_counts["Medium"] += 1

                    sev_labels = list(severity_counts.keys())
                    sev_values = list(severity_counts.values())
                    sev_colors = ['#EF4444', '#F59E0B', '#3B82F6']

                    fig_bar = go.Figure(data=[go.Bar(
                        x=sev_labels, y=sev_values,
                        marker_color=sev_colors,
                        text=sev_values, textposition='outside',
                        textfont=dict(color='#E8EDF5', size=11, family='JetBrains Mono')
                    )])
                    fig_bar.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#E8EDF5',
                        xaxis=dict(showgrid=False, color='#4A6080'),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color='#4A6080'),
                        margin=dict(t=10, b=10, l=10, r=10), height=190,
                        showlegend=False
                    )
                    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No gaps detected yet.")

        # ─── Horizontal Pipeline Stepper ───
        def draw_h_pipeline():
            steps_def = [
                ("📋", "Policy Agent", "Document ingestion", "01"),
                ("💬", "Sentiment Agent", "NLP scoring", "02"),
                ("🔗", "Clustering Agent", "Theme grouping", "03"),
                ("⚠️", "Gap Agent", "Coverage audit", "04"),
                ("💡", "Recommendation", "Action synthesis", "05"),
                ("📝", "Survey Agent", "Feedback design", "06"),
            ]

            html = '<div style="background:#111827; border:1px solid rgba(255,255,255,0.07); border-radius:12px; padding:18px 16px; margin-bottom:1rem;">'
            html += '<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;">'
            html += '<div><div class="section-header">Multi-Agent Analysis Pipeline</div>'
            html += '<div class="section-sub" style="margin-bottom:0;">Sequential AI processing chain</div></div>'

            all_done = all(initial_statuses.get(s[3]) == "Done" for s in steps_def[:5])
            if all_done:
                html += '<span class="badge badge-teal">COMPLETE</span>'
            else:
                html += '<span class="badge badge-amber">READY</span>'
            html += '</div>'

            html += '<div class="h-pipeline">'
            for i, (icon, name, desc, key) in enumerate(steps_def):
                status = initial_statuses.get(key, "Waiting")
                card_class = "complete" if status == "Done" else "active" if status == "Running" else "queued"

                icon_bg = "rgba(45,212,191,0.15)" if status == "Done" else "rgba(245,158,11,0.15)" if status == "Running" else "rgba(255,255,255,0.05)"
                icon_color = "#2DD4BF" if status == "Done" else "#F59E0B" if status == "Running" else "#3D5070"
                dot_color = "#2DD4BF" if status == "Done" else "#F59E0B" if status == "Running" else "#1E2D40"
                name_color = "#E8EDF5" if status in ["Done", "Running"] else "#3D5070"
                badge_bg = "rgba(45,212,191,0.10)" if status == "Done" else "rgba(245,158,11,0.10)" if status == "Running" else "rgba(255,255,255,0.04)"
                badge_color = "#2DD4BF" if status == "Done" else "#F59E0B" if status == "Running" else "#3D5070"
                badge_text = "Complete" if status == "Done" else "Running" if status == "Running" else "Optional" if status == "Optional" else "Queued"

                html += '<div class="h-pipeline-step">'
                html += f'<div class="h-pipeline-card {card_class}">'
                html += f'<div><span class="h-pipeline-icon" style="background:{icon_bg};">{icon}</span>'
                html += f'<span class="h-pipeline-dot" style="background:{dot_color};"></span></div>'
                html += f'<div class="h-pipeline-name" style="color:{name_color};">{name}</div>'
                html += f'<div class="h-pipeline-desc">{desc}</div>'
                html += f'<span class="h-pipeline-badge" style="background:{badge_bg}; color:{badge_color};">{badge_text}</span>'
                html += '</div>'

                if i < len(steps_def) - 1:
                    arrow_color = "#2DD4BF" if status == "Done" else "#F59E0B" if status == "Running" else "#1E2D40"
                    html += f'<div class="h-pipeline-arrow" style="color:{arrow_color};">→</div>'

                html += '</div>'

            html += '</div></div>'
            return html

        st.markdown(draw_h_pipeline(), unsafe_allow_html=True)

    # ─────── TABBED RESULTS ───────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Policy Overview",
        "🗣️ Public Concerns",
        "⚠️ Policy Gaps",
        "💡 Recommendations",
        "📝 Executive Memo",
        "📋 Survey Blueprint"
    ])

    # ─── TAB 1: POLICY OVERVIEW ───
    with tab1:
        if res:
            pol = res.get('policy_analysis', {})
            policy_title = sanitize_html(pol.get('policy_title', 'Unnamed Policy'))

            with st.container(border=True):
                st.markdown(f"#### 📋 {policy_title}")
                st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:8px 0;"></div>', unsafe_allow_html=True)

                st.markdown("##### Core Extracted Rules")
                for r in pol.get('main_rules', []):
                    st.markdown(f"- {sanitize_html(r)}")

                cols = st.columns(2)
                with cols[0]:
                    st.markdown("##### 🎯 Affected Groups")
                    for group in pol.get('affected_groups', []):
                        st.markdown(f"- {sanitize_html(group)}")
                with cols[1]:
                    st.markdown("##### ⚖️ Penalties & Enforcement")
                    for penalty in pol.get('penalties', []):
                        st.markdown(f"- {sanitize_html(penalty)}")

                unclear = pol.get('unclear_clauses', [])
                if unclear:
                    st.markdown("##### ❓ Unclear or Ambiguous Clauses")
                    for item in unclear:
                        st.warning(f"**Unclear:** {sanitize_html(item)}")
        else:
            st.info("Run 'Analyze Public Feedback' to populate this tab.")

    # ─── TAB 2: PUBLIC CONCERNS ───
    with tab2:
        if res:
            concern_data = res.get('concern_analysis', {})
            concerns = concern_data.get('concern_clusters', concern_data.get('top_concerns', []))

            with st.container(border=True):
                st.markdown('<div class="section-header">Public Concerns & Theme Frequency</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-sub">Clustered stakeholder feedback patterns</div>', unsafe_allow_html=True)

                if concerns:
                    themes = [c.get('theme', 'N/A') for c in concerns]
                    counts = [c.get('count', 0) for c in concerns]

                    df_chart = pd.DataFrame({"Concern Theme": themes, "Comments Count": counts})
                    df_chart = df_chart.sort_values(by="Comments Count", ascending=True)

                    fig_bar = px.bar(
                        df_chart, x="Comments Count", y="Concern Theme",
                        orientation='h', color="Comments Count",
                        color_continuous_scale=['#3B82F6', '#2DD4BF']
                    )
                    fig_bar.update_layout(
                        coloraxis_showscale=False,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#E8EDF5',
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)'),
                        yaxis=dict(showgrid=False),
                        margin=dict(t=5, b=5, l=5, r=5), height=240
                    )
                    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

                    st.markdown("##### 🗣️ Theme Clusters & Evidence Quotes")

                    for c in concerns:
                        theme = sanitize_html(c.get('theme', 'Theme'))
                        count = c.get('count', 0)
                        urgency = sanitize_html(c.get('urgency_level', c.get('urgency', 'Medium'))).strip().lower()

                        if urgency in ["high", "critical"]:
                            urgency_md = f":red[● {urgency.upper()}]"
                        elif urgency == "medium":
                            urgency_md = f":orange[● {urgency.upper()}]"
                        else:
                            urgency_md = f":blue[● {urgency.upper()}]"

                        with st.expander(f"{theme} ({count} comments)"):
                            st.markdown(f"**Urgency:** {urgency_md}")
                            st.markdown("**Evidence Quotes from Stakeholders:**")
                            for quote in c.get('sample_comments', c.get('evidence', [])):
                                st.markdown(
                                    f'<div class="evidence-quote">{sanitize_html(quote)}</div>',
                                    unsafe_allow_html=True
                                )
                else:
                    st.write("No major concern clusters identified.")
        else:
            st.info("Run 'Analyze Public Feedback' to populate this tab.")

    # ─── TAB 3: POLICY GAPS ───
    with tab3:
        if res:
            gaps_data = res.get('gap_analysis', {})
            gaps = gaps_data.get('gaps', gaps_data.get('policy_gaps', []))

            with st.container(border=True):
                st.markdown('<div class="section-header">Identified Policy Gaps & Exclusions</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-sub">Policy clauses audited against design principles and active complaints</div>', unsafe_allow_html=True)

                if gaps:
                    for g in gaps:
                        concern = sanitize_html(g.get('concern', g.get('public_concern', g.get('theme', g.get('policy_principle', g.get('relevant_policy_principle', 'N/A'))))))
                        covered = g.get('covered_in_policy', g.get('covered', None))

                        if covered is None:
                            policy_status_str = str(g.get('policy_status', '')).lower()
                            if 'cover' in policy_status_str or 'yes' in policy_status_str or 'true' in policy_status_str:
                                covered = True
                            elif 'omission' in policy_status_str or 'gap' in policy_status_str or 'no' in policy_status_str or 'false' in policy_status_str:
                                covered = False
                            else:
                                covered = False

                        desc = sanitize_html(g.get('gap_description', g.get('description', 'N/A')))
                        severity = sanitize_html(g.get('severity', '')).strip().lower()
                        suggested_fix = sanitize_html(g.get('suggested_fix', g.get('fix', '')))
                        relevant_principle = sanitize_html(g.get('relevant_policy_principle', g.get('policy_principle', '')))

                        with st.container(border=True):
                            st.markdown(f"#### {concern}")

                            status_md = get_status_markdown(covered)
                            severity_md = get_severity_markdown(severity)

                            badge_str = f"**Status:** {status_md}"
                            if severity_md:
                                badge_str += f"  |  **Severity:** {severity_md}"
                            st.markdown(badge_str)

                            st.markdown(f"**Detected Gap:** {desc}")

                            if suggested_fix:
                                st.markdown(f"**Suggested Fix:** {suggested_fix}")
                            if relevant_principle and relevant_principle != concern:
                                st.markdown(f"**Relevant Principle:** {relevant_principle}")
                else:
                    st.info("No major policy gaps were detected.")
        else:
            st.info("Run 'Analyze Public Feedback' to populate this tab.")

    # ─── TAB 4: RECOMMENDATIONS ───
    with tab4:
        if res:
            recs_data = res.get('recommendations', {})
            rec_list = recs_data.get('recommendations', recs_data.get('recommended_changes', []))
            revised_clauses = recs_data.get('revised_policy_suggestions', recs_data.get('revised_clauses', []))
            questions = recs_data.get('meeting_questions', [])

            with st.container(border=True):
                st.markdown('<div class="section-header">Actionable Policy Modifications</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-sub">Priority-ranked recommendations from multi-agent synthesis</div>', unsafe_allow_html=True)

                critical = []
                important = []
                nice_to_have = []

                for r in rec_list:
                    prio = r.get('priority', r.get('rank', 'Important')).lower()
                    if 'crit' in prio:
                        critical.append(r)
                    elif 'nice' in prio or 'low' in prio:
                        nice_to_have.append(r)
                    else:
                        important.append(r)

                cols_rec = st.columns(3)

                with cols_rec[0]:
                    st.markdown("#### :red[🔴 Critical]")
                    if critical:
                        for item in critical:
                            act = sanitize_html(item.get('action', item.get('recommendation', 'N/A')))
                            group = sanitize_html(item.get('affected_group', ''))
                            st.markdown(f"- **{act}**")
                            if group:
                                st.markdown(f"  *Target:* :violet[{group}]")
                    else:
                        st.caption("No critical items.")

                with cols_rec[1]:
                    st.markdown("#### :orange[🟠 Important]")
                    if important:
                        for item in important:
                            act = sanitize_html(item.get('action', item.get('recommendation', 'N/A')))
                            group = sanitize_html(item.get('affected_group', ''))
                            st.markdown(f"- **{act}**")
                            if group:
                                st.markdown(f"  *Target:* :violet[{group}]")
                    else:
                        st.caption("No important items.")

                with cols_rec[2]:
                    st.markdown("#### :blue[🔵 Nice-to-Have]")
                    if nice_to_have:
                        for item in nice_to_have:
                            act = sanitize_html(item.get('action', item.get('recommendation', 'N/A')))
                            group = sanitize_html(item.get('affected_group', ''))
                            st.markdown(f"- **{act}**")
                            if group:
                                st.markdown(f"  *Target:* :violet[{group}]")
                    else:
                        st.caption("No nice-to-have items.")

                st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:16px 0;"></div>', unsafe_allow_html=True)

                if revised_clauses:
                    st.markdown("##### ✏️ Drafted Clause Revisions")
                    st.caption("Suggested redlines for the next document version.")
                    for c in revised_clauses:
                        st.info(sanitize_html(c))

                if questions:
                    st.markdown("##### 💬 Stakeholder Dialogue Starters")
                    st.caption("Suggested agenda items for the next policy review.")
                    for q in questions:
                        st.markdown(f"🗣️ **{sanitize_html(q)}**")
        else:
            st.info("Run 'Analyze Public Feedback' to populate this tab.")

    # ─── TAB 5: EXECUTIVE MEMO ───
    with tab5:
        if res:
            recs_data = res.get('recommendations', {})
            memo = recs_data.get('executive_memo', recs_data.get('memo', ''))

            if not memo:
                policy_title = res.get('policy_analysis', {}).get('policy_title', 'Draft Policy')
                memo = f"""### MEMORANDUM

**TO:** Executive Policy Committee  
**FROM:** PolicyPulse AI Civic Intelligence Suite  
**DATE:** {pd.Timestamp.now().strftime('%B %d, %Y')}  
**SUBJECT:** Stakeholder Consultation Summary - {policy_title}  

***

#### Executive Summary
We have completed a multi-agent consultation synthesis of the proposed draft: **{policy_title}** against submitted stakeholder feedback. Sentiment analysis reflects an active dialogue between rules enforcement and public accommodations constraints.

#### Key Findings
Our concern clustering agents mapped several critical public themes, specifically relating to missing protections. A cross-reference against design principles identified significant policy gaps in enforcement exceptions, appeals pathways, and accommodations metrics.

#### Strategic Recommendations
We suggest amending the current rules framework immediately. Detailed revised wording, prioritized task items, and stakeholder meeting question banks have been compiled and are visible in the Consultation Dashboard.
"""

            clean_memo = sanitize_html(memo)

            # Formal memo container
            st.markdown(
                '<div class="memo-container">'
                '<div class="memo-letterhead">'
                '<div class="memo-org">PolicyPulse AI — Civic Intelligence Suite</div>'
                f'<div class="memo-date">{pd.Timestamp.now().strftime("%B %d, %Y")}</div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

            with st.container(border=True):
                st.markdown(clean_memo)

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "📥 Download Briefing (Markdown)",
                    data=clean_memo,
                    file_name="policypulse_executive_memo.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with c2:
                st.download_button(
                    "📥 Download Briefing (Text)",
                    data=clean_memo,
                    file_name="policypulse_executive_memo.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("Run 'Analyze Public Feedback' to populate this tab.")

    # ─── TAB 6: SURVEY GENERATOR ───
    with tab6:
        if surv:
            title = sanitize_html(surv.get("title", surv.get("survey_title", "Policy Feedback Survey")))
            description = sanitize_html(surv.get("description", surv.get("survey_description", "")))

            with st.container(border=True):
                st.markdown(f"#### {title}")
                if description:
                    st.markdown(f"*{description}*")
                st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:10px 0;"></div>', unsafe_allow_html=True)

                # Render sections & questions as cards
                sections = surv.get("sections", [])
                if not sections and surv.get("questions"):
                    sections = [{
                        "section_name": "Survey Questions",
                        "questions": [
                            {
                                "question": q.get("question_text", q.get("question", "")),
                                "type": q.get("question_type", q.get("type", "text")),
                                "options": q.get("options", [])
                            } for q in surv.get("questions", [])
                        ]
                    }]

                q_counter = 0
                for s_idx, section in enumerate(sections):
                    sec_name = sanitize_html(section.get("section_name", f"Section {s_idx+1}"))
                    st.markdown(f"##### {sec_name}")

                    for q_idx, q in enumerate(section.get("questions", [])):
                        q_counter += 1
                        q_text = sanitize_html(q.get("question", ""))
                        q_type = sanitize_html(q.get("type", "text")).lower()
                        q_opts = [sanitize_html(opt) for opt in q.get("options", [])]

                        # Type badge color
                        type_bg = "rgba(45,212,191,0.10)" if q_type == "multiple_choice" else "rgba(245,158,11,0.10)" if q_type == "rating" else "rgba(59,130,246,0.10)"
                        type_color = "#2DD4BF" if q_type == "multiple_choice" else "#F59E0B" if q_type == "rating" else "#3B82F6"
                        type_label = q_type.replace("_", " ").title()

                        card_html = (
                            f'<div class="survey-q-card">'
                            f'<div class="survey-q-num">Question {q_counter}</div>'
                            f'<div class="survey-q-text">{q_text}</div>'
                            f'<span class="survey-q-type" style="background:{type_bg}; color:{type_color}; border:1px solid {type_color}33;">{type_label}</span>'
                        )

                        if q_opts:
                            card_html += '<div style="margin-top:10px;">'
                            for opt in q_opts:
                                card_html += f'<div class="survey-q-option">○ {opt}</div>'
                            card_html += '</div>'

                        card_html += '</div>'
                        st.markdown(card_html, unsafe_allow_html=True)

                # Setup instructions
                st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:14px 0;"></div>', unsafe_allow_html=True)
                steps = surv.get("google_forms_steps", surv.get("setup_instructions", []))
                if steps:
                    st.markdown("##### 🛠️ Google Forms Manual Setup")
                    for step in steps:
                        st.write("• " + sanitize_html(step))

            # Download Button
            st.download_button(
                "📥 Download Survey JSON",
                json.dumps(surv, indent=2),
                file_name="survey.json",
                mime="application/json",
                use_container_width=True
            )

            # One-Click Deployment
            st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:16px 0;"></div>', unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown('<div class="section-header">🚀 One-Click Google Form Deployment</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-sub">Instantly create a live Google Form from the generated survey blueprint.</div>', unsafe_allow_html=True)

                if st.button("Deploy Google Form →", use_container_width=True):
                    with st.spinner("Creating Google Form..."):
                        result = survey_agent.deploy_google_form(surv)

                    if result.get("url"):
                        st.success("Google Form Created Successfully 🎉")
                        st.markdown(f"**🔗 Live Form:** [{result['url']}]({result['url']})")
                        if result.get("edit_url"):
                            st.markdown(f"**✏️ Edit Link:** [{result['edit_url']}]({result['edit_url']})")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        st.error(f"Form creation failed: {error_msg}")
        else:
            st.info("Click 'Generate Feedback Survey Blueprint' to create a structured Google Forms setup blueprint based on your loaded policy document.")

if __name__ == "__main__":
    pass
