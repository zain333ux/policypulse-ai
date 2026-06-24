import streamlit as st
import pandas as pd
import json
import io
import plotly.graph_objects as go
import plotly.express as px
import textwrap
from dotenv import load_dotenv

load_dotenv()

import importlib
import src.utils.llm_client
import src.agents.policy_extraction_agent
import src.agents.sentiment_agent
import src.agents.concern_clustering_agent
import src.agents.gap_detection_agent
import src.agents.recommendation_agent
import src.agents.survey_generator_agent
import src.agents.pipeline

importlib.reload(src.utils.llm_client)
importlib.reload(src.agents.policy_extraction_agent)
importlib.reload(src.agents.sentiment_agent)
importlib.reload(src.agents.concern_clustering_agent)
importlib.reload(src.agents.gap_detection_agent)
importlib.reload(src.agents.recommendation_agent)
importlib.reload(src.agents.survey_generator_agent)
importlib.reload(src.agents.pipeline)

from src.agents.pipeline import run_pipeline, run_survey_generation
from src.agents.policy_extraction_agent import extract_policy_details
from src.agents.sentiment_agent import analyze_sentiment
from src.agents.concern_clustering_agent import cluster_concerns
from src.agents.gap_detection_agent import detect_gaps
from src.agents.recommendation_agent import generate_recommendations
import src.agents.survey_generator_agent as survey_agent
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
    :root {{
        --bg-base:      #0B1220;
        --bg-surface:   #111827;
        --bg-raised:    #1F2937;
        --bg-hover:     #1F2D44;
        --cyan:         #38BDF8;
        --cyan-dim:     #0284C7;
        --cyan-glow:    rgba(56, 189, 248, 0.12);
        --cyan-border:  rgba(56, 189, 248, 0.2);
        --cyan-strong:  rgba(56, 189, 248, 0.5);
        --purple:       #8B5CF6;
        --purple-dim:   rgba(139, 92, 246, 0.15);
        --green:        #10B981;
        --green-dim:    rgba(16, 185, 129, 0.15);
        --red:          #EF4444;
        --red-dim:      rgba(239, 68, 68, 0.15);
        --amber:        #F59E0B;
        --ink:          #E8EDF5;
        --ink-bright:   #FFFFFF;
        --ink-muted:    #6B7FA3;
        --ink-faint:    rgba(255, 255, 255, 0.08);
    }}
    .stApp {{
        background-image: linear-gradient(rgba(11, 18, 32, 0.9), rgba(11, 18, 32, 0.9)), url(data:image/{bg_ext};base64,{bg_base64}) !important;
        background-attachment: fixed !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
        overflow-x: hidden !important;
    }}
    """
else:
    bg_style = """
    :root {
        --bg-base:      #0B1220;
        --bg-surface:   #111827;
        --bg-raised:    #1F2937;
        --bg-hover:     #1F2D44;
        --cyan:         #38BDF8;
        --cyan-dim:     #0284C7;
        --cyan-glow:    rgba(56, 189, 248, 0.12);
        --cyan-border:  rgba(56, 189, 248, 0.2);
        --cyan-strong:  rgba(56, 189, 248, 0.5);
        --purple:       #8B5CF6;
        --purple-dim:   rgba(139, 92, 246, 0.15);
        --green:        #10B981;
        --green-dim:    rgba(16, 185, 129, 0.15);
        --red:          #EF4444;
        --red-dim:      rgba(239, 68, 68, 0.15);
        --amber:        #F59E0B;
        --ink:          #E8EDF5;
        --ink-bright:   #FFFFFF;
        --ink-muted:    #6B7FA3;
        --ink-faint:    rgba(255, 255, 255, 0.08);
    }
    .stApp {
        background-color: var(--bg-base) !important;
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
        overflow-x: hidden !important;
    }
    """

st.markdown(f"<style>{bg_style}</style>", unsafe_allow_html=True)

# ==========================================
# DESIGN SYSTEM CSS (Figma Tokens)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

    /* ─── Cyberpunk Animations ─── */
    @keyframes pulse-cyan {
        0%, 100% { box-shadow: 0 0 8px var(--cyan-glow), inset 0 0 8px var(--cyan-glow); }
        50%       { box-shadow: 0 0 22px rgba(56,189,248,0.28), inset 0 0 14px rgba(56,189,248,0.1); }
    }
    @keyframes scan-line {
        0%   { transform: translateY(-100%); opacity: 0; }
        15%  { opacity: 0.4; }
        85%  { opacity: 0.4; }
        100% { transform: translateY(1000%); opacity: 0; }
    }
    @keyframes blink-cursor {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0; }
    }
    @keyframes flicker-in {
        0%   { opacity: 0; }
        20%  { opacity: 0.8; }
        40%  { opacity: 0.3; }
        60%  { opacity: 1; }
        80%  { opacity: 0.7; }
        100% { opacity: 1; }
    }
    @keyframes slide-up {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes slide-right {
        from { opacity: 0; transform: translateX(-12px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes glow-pulse {
        0%, 100% { text-shadow: 0 0 8px rgba(56,189,248,0.6); }
        50%       { text-shadow: 0 0 24px rgba(56,189,248,0.9), 0 0 48px rgba(56,189,248,0.3); }
    }
    @keyframes border-rotate {
        0%   { background-position: 0% 0%; }
        100% { background-position: 200% 0%; }
    }
    @keyframes dot-blink {
        0%, 100% { opacity: 1; }
        33%       { opacity: 0.2; }
        66%       { opacity: 0.7; }
    }
    @keyframes rotate-slow {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }
    @keyframes status-ping {
        0%   { box-shadow: 0 0 0 0 rgba(56,189,248,0.7); }
        70%  { box-shadow: 0 0 0 8px rgba(56,189,248,0); }
        100% { box-shadow: 0 0 0 0 rgba(56,189,248,0); }
    }
    @keyframes status-ping-cyan {
        0%   { box-shadow: 0 0 0 0 rgba(56,189,248,0.7); }
        70%  { box-shadow: 0 0 0 8px rgba(56,189,248,0); }
        100% { box-shadow: 0 0 0 0 rgba(56,189,248,0); }
    }
    @keyframes status-ping-amber {
        0%   { box-shadow: 0 0 0 0 rgba(255,203,61,0.7); }
        70%  { box-shadow: 0 0 0 8px rgba(255,203,61,0); }
        100% { box-shadow: 0 0 0 0 rgba(255,203,61,0); }
    }
    .status-dot-green {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--cyan);
        animation: status-ping 1.8s ease-in-out infinite;
        display: inline-block;
        vertical-align: middle;
        flex-shrink: 0;
    }
    @keyframes status-ping-blue {
        0%   { box-shadow: 0 0 0 0 rgba(59,130,246,0.7); }
        70%  { box-shadow: 0 0 0 8px rgba(59,130,246,0); }
        100% { box-shadow: 0 0 0 0 rgba(59,130,246,0); }
    }
    .status-dot-blue {
        width: 6px; height: 6px; border-radius: 50%;
        background: #3B82F6;
        animation: status-ping-blue 1.8s ease-in-out infinite;
        display: inline-block;
        vertical-align: middle;
        flex-shrink: 0;
    }
    .status-dot-amber {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--amber);
        animation: status-ping-amber 1.8s ease-in-out infinite;
        display: inline-block;
        vertical-align: middle;
        flex-shrink: 0;
    }
    .status-dot-cyan {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--cyan);
        animation: status-ping-cyan 1.8s ease-in-out infinite;
        display: inline-block;
        vertical-align: middle;
        flex-shrink: 0;
    }
    @keyframes arrow-flow {
        0%, 100% { transform: translateX(0); opacity: 0.5; }
        50%       { transform: translateX(4px); opacity: 1; text-shadow: 0 0 8px currentColor; }
    }
    .arrow-flow {
        display: inline-block;
        animation: arrow-flow 1.5s ease-in-out infinite;
    }
    @keyframes mega-glow {
        0%, 100% {
            text-shadow: 0 0 10px rgba(56,189,248,0.6), 0 0 20px rgba(56,189,248,0.4), 0 0 40px rgba(56,189,248,0.2);
        }
        50% {
            text-shadow: 0 0 20px rgba(56,189,248,1), 0 0 40px rgba(56,189,248,0.7), 0 0 80px rgba(56,189,248,0.4), 0 0 120px rgba(124,58,255,0.3);
        }
    }
    @keyframes float-y {
        0%, 100% { transform: translateY(0); }
        50%       { transform: translateY(-8px); }
    }
    @keyframes float-y2 {
        0%, 100% { transform: translateY(0); }
        50%       { transform: translateY(-5px); }
    }
    @keyframes badge-shimmer {
        0%   { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes sb-glow-pulse {
        0%, 100% { box-shadow: 0 0 0 rgba(56,189,248,0); }
        50%       { box-shadow: 0 0 18px rgba(56,189,248,0.15); }
    }
    @keyframes sidebar-scan {
        0%   { top: -10%; opacity: 0; }
        10%  { opacity: 0.6; }
        90%  { opacity: 0.6; }
        100% { top: 110%; opacity: 0; }
    }
    @keyframes logo-flicker {
        0%, 92%, 100% { opacity: 1; }
        93%           { opacity: 0.4; }
        95%           { opacity: 1; }
        97%           { opacity: 0.2; }
        99%           { opacity: 1; }
    }
    @keyframes flow-card-lift {
        0%, 100% { transform: translateY(0); box-shadow: 0 0 0 rgba(56,189,248,0); }
        33%       { transform: translateY(-6px); box-shadow: 0 12px 28px rgba(56,189,248,0.12); }
    }
    @keyframes tag-glow-cycle {
        0%, 100% { box-shadow: 0 0 6px currentColor; }
        50%       { box-shadow: 0 0 16px currentColor; }
    }

    /* ─── Reset & Base ─── */
    html, body, [class*="css"] {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ─── Layout ─── */
    .block-container {
        max-width: 1280px !important;
        padding-top: 0rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin: 0 auto !important;
    }

    /* ─── Hide Streamlit chrome ─── */
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none;
    }
    header[data-testid="stHeader"] * {
        pointer-events: auto;
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* ─── Figma Top Header Bar ─── */
    .figma-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 0 14px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--cyan-border);
    }
    .figma-topbar-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 17px;
        font-weight: 600;
        color: var(--ink-bright);
        display: flex;
        align-items: center;
        gap: 8px;
        text-shadow: 0 0 10px var(--cyan-glow);
    }
    .figma-topbar-live {
        display: inline-block;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 500;
        font-family: 'Space Grotesk', sans-serif;
        background: var(--cyan-glow);
        color: var(--cyan);
        border: 1px solid var(--cyan-border);
        letter-spacing: 1px;
        animation: pulse-cyan 3s ease-in-out infinite;
    }
    .figma-topbar-sub {
        font-size: 12px;
        color: var(--ink-muted);
        margin-top: 2px;
    }
    .figma-topbar-right {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .figma-search-box {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 7px 12px;
        background: var(--bg-raised);
        border: 1px solid var(--cyan-border);
        border-radius: 4px;
        font-size: 13px;
        color: var(--ink-muted);
    }
    .figma-export-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 14px;
        background: transparent;
        border: 1px solid var(--cyan);
        color: var(--cyan);
        border-radius: 4px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 0 12px rgba(56,189,248,0.1);
        transition: all 0.15s ease;
    }
    .figma-export-btn:hover {
        background: var(--cyan-glow);
        box-shadow: 0 0 20px rgba(56,189,248,0.25);
    }

    /* ─── Sidebar Toggle Buttons ─── */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        position: fixed !important; top: 16px !important; left: 12px !important;
        z-index: 999999 !important; background: var(--bg-surface) !important;
        border: 1px solid var(--cyan-border) !important; border-radius: 6px !important;
        width: 42px !important; height: 42px !important;
        box-shadow: 0 0 14px var(--cyan-glow) !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapseButton"] button {
        background: transparent !important; border: none !important; box-shadow: none !important;
        width: 42px !important; height: 42px !important; padding: 0 !important;
        color: transparent !important; font-size: 0 !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        position: relative !important;
    }
    [data-testid="stSidebarCollapsedControl"] button svg,
    [data-testid="stSidebarCollapseButton"] button svg { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] button::before,
    [data-testid="stSidebarCollapseButton"] button::before {
        content: "" !important; display: block !important; width: 16px !important; height: 2px !important;
        background: var(--cyan) !important; border-radius: 1px !important;
        box-shadow: 0 5px 0 var(--cyan), 0 10px 0 var(--cyan) !important;
        position: absolute !important; top: 50% !important; left: 50% !important;
        transform: translate(-50%, -5px) !important;
    }

    /* ─── Sidebar ─── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #070D19 0%, #0B1426 50%, #070D19 100%) !important;
        border-right: 1px solid var(--cyan-border) !important;
        box-shadow: 4px 0 40px rgba(56,189,248,0.08) !important;
        position: relative;
        overflow: hidden;
    }
    section[data-testid="stSidebar"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 320px; height: 100vh;
        background-image:
            linear-gradient(rgba(56,189,248,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(56,189,248,0.02) 1px, transparent 1px);
        background-size: 18px 18px;
        pointer-events: none;
        z-index: 0;
    }

    section[data-testid="stSidebar"] > div:first-child {
        background-color: transparent !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li {
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ─── Hero Title (kept for compat) ─── */
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--ink-bright);
        margin-bottom: 2px;
    }
    .hero-subtitle {
        font-size: 0.8rem;
        color: var(--ink-muted);
        margin-bottom: 16px;
        font-family: 'Inter', sans-serif;
    }

    /* ─── Section Headers ─── */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--cyan);
        margin-bottom: 3px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .section-sub {
        font-size: 0.72rem;
        color: var(--ink-muted);
        margin-bottom: 12px;
    }

    /* ─── Badges ─── */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 2px;
        font-size: 10px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        animation: tag-glow-cycle 3s ease-in-out infinite;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
    }
    .badge:hover {
        transform: scale(1.08) translateY(-1px);
        box-shadow: 0 0 12px currentColor;
        filter: brightness(1.2);
    }
    .badge-teal   { border: 1px solid rgba(59, 130, 246, 0.2); color: #3B82F6; }
    .badge-blue   { border: 1px solid rgba(147,197,253,0.4); color: #93C5FD; }
    .badge-violet { border: 1px solid var(--purple-dim); color: var(--purple); }
    .badge-coral  { border: 1px solid var(--red-dim); color: var(--red); }
    .badge-amber  { border: 1px solid rgba(245,158,11,0.4); color: var(--amber); }
    .badge-gray   { border: 1px solid var(--ink-faint); color: var(--ink-muted); }

    /* ─── Figma Card ─── */
    .figma-card {
        background: var(--bg-surface) !important;
        border: 1px solid var(--cyan-border) !important;
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.18s ease;
        animation: slide-up 0.35s ease-out;
    }
    .figma-card:hover {
        border-color: var(--cyan-strong) !important;
        box-shadow: 0 0 20px var(--cyan-glow) !important;
    }
    .figma-card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: var(--cyan);
        margin-bottom: 2px;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-shadow: 0 0 8px var(--cyan-glow);
    }
    .figma-card-sub {
        font-size: 12px;
        color: var(--ink-muted);
        margin-bottom: 14px;
    }

    /* ─── KPI Cards ─── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 16px;
    }
    .kpi-card {
        background: var(--bg-surface) !important;
        border: 1px solid var(--cyan-border) !important;
        border-radius: 4px !important;
        padding: 20px !important;
        box-shadow: 0 0 14px rgba(56,189,248,0.04) !important;
        transition: all 0.18s ease !important;
    }
    .kpi-card:hover {
        border-color: var(--cyan-strong) !important;
        box-shadow: 0 0 20px var(--cyan-glow) !important;
        transform: translateY(-4px) scale(1.02) !important;
    }
    .kpi-grid .kpi-card:nth-child(1) { animation: slide-up 0.4s ease both, float-y 5s ease-in-out infinite; animation-delay: 0s, 0s; }
    .kpi-grid .kpi-card:nth-child(2) { animation: slide-up 0.5s ease both, float-y 5s ease-in-out infinite; animation-delay: 0.1s, 1.25s; }
    .kpi-grid .kpi-card:nth-child(3) { animation: slide-up 0.6s ease both, float-y 5s ease-in-out infinite; animation-delay: 0.2s, 2.5s; }
    .kpi-grid .kpi-card:nth-child(4) { animation: slide-up 0.7s ease both, float-y 5s ease-in-out infinite; animation-delay: 0.3s, 3.75s; }

    .kpi-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .kpi-label {
        font-family: 'Inter', sans-serif !important;
        color: var(--ink-muted) !important;
        font-size: 0.65rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }
    .kpi-icon {
        width: 28px;
        height: 28px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        transition: all 0.3s ease;
    }
    .kpi-card:hover .kpi-icon {
        transform: rotate(10deg) scale(1.1);
    }
    .kpi-value {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--cyan) !important;
        font-size: 1.8rem !important;
        text-shadow: 0 0 16px var(--cyan-glow) !important;
    }
    .kpi-delta { display: flex; align-items: center; gap: 5px; font-size: 11px; }
    .kpi-delta-sub { color: var(--ink-muted); font-size: 11px; }

    /* ─── Charts Row ─── */
    .charts-row {
        display: grid;
        grid-template-columns: 2fr 3fr;
        gap: 16px;
        margin-bottom: 16px;
    }
    .chart-card {
        background: var(--bg-surface) !important;
        border: 1px solid var(--cyan-border) !important;
        border-radius: 6px !important;
        padding: 20px !important;
        transition: all 0.18s ease !important;
        animation: slide-up 0.5s ease-out both;
    }
    .chart-card:hover {
        border-color: var(--cyan-strong) !important;
        box-shadow: 0 0 20px var(--cyan-glow) !important;
    }
    .chart-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 16px;
    }
    .chart-header-badge {
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 2px;
        background: var(--bg-raised);
        color: var(--ink-muted);
        font-family: 'Share Tech Mono', monospace;
        border: 1px solid var(--ink-faint);
    }
    .chart-header-link {
        font-size: 12px;
        color: var(--cyan);
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 3px;
    }
    .donut-row {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    .donut-legend {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .donut-legend-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .donut-legend-left {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .donut-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .donut-legend-label {
        font-size: 12px;
        color: var(--ink-muted);
    }
    .donut-legend-value {
        font-size: 12px;
        font-weight: 500;
        color: var(--ink);
        font-family: 'Share Tech Mono', monospace;
    }
    .bar-legend {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-top: 8px;
    }
    .bar-legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 10px;
        color: var(--ink-muted);
    }
    .bar-legend-swatch {
        width: 8px;
        height: 8px;
        border-radius: 2px;
    }

    /* ─── Horizontal Pipeline Stepper ─── */
    .h-pipeline {
        display: flex;
        align-items: stretch;
        gap: 0;
        margin-bottom: 0;
        width: 100%;
    }
    .h-pipeline-step { flex: 1; display: flex; align-items: center; }
    .h-pipeline-card {
        flex: 1;
        border-radius: 6px;
        padding: 14px 12px;
        min-height: 108px;
        border: 1px solid var(--cyan-border);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .h-pipeline-card::before {
        content: ""; position: absolute; top: 0; left: -60%; width: 40%; height: 100%;
        background: linear-gradient(120deg, transparent, var(--cyan-glow), transparent);
        transform: skewX(-20deg); animation: badge-shimmer 4s linear infinite;
        pointer-events: none;
    }
    .h-pipeline-card.complete {
        background: rgba(59, 130, 246, 0.08) !important;
        border-color: rgba(59, 130, 246, 0.2) !important;
        color: #3B82F6 !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.15) !important;
        animation: flow-card-lift 4s ease-in-out infinite;
    }
    .h-pipeline-card.complete:nth-child(even) {
        animation-delay: 0.6s;
    }
    .h-pipeline-card.active {
        background: var(--cyan-glow) !important;
        border-color: var(--cyan-border) !important;
        color: var(--cyan) !important;
        box-shadow: 0 0 14px var(--cyan-glow) !important;
        animation: pulse-cyan 2s ease-in-out infinite, flow-card-lift 4s ease-in-out infinite;
        animation-delay: 0s, 1.3s;
    }
    .h-pipeline-card.queued {
        background: var(--bg-surface) !important;
        border-color: var(--ink-faint) !important;
        color: var(--ink-muted) !important;
        animation: flow-card-lift 4s ease-in-out infinite;
        animation-delay: 2.6s;
    }
    .h-pipeline-card.optional {
        background: var(--bg-surface) !important;
        border-color: var(--ink-faint) !important;
        color: var(--ink-muted) !important;
    }
    .h-pipeline-icon {
        width: 24px; height: 24px; border-radius: 4px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 11px; margin-right: 6px; vertical-align: middle;
    }
    .h-pipeline-dot {
        width: 7px; height: 7px; border-radius: 50%;
        display: inline-block; vertical-align: middle; margin-left: 4px;
    }
    .h-pipeline-card.active .h-pipeline-dot {
        animation: status-ping-cyan 1.5s ease-in-out infinite !important;
    }
    .h-pipeline-name { font-size: 11.5px; font-weight: 600; margin-top: 6px; }
    .h-pipeline-desc { font-size: 9.5px; color: var(--ink-muted); margin-top: 2px; line-height: 1.3; }
    .h-pipeline-badge {
        display: inline-block; font-size: 8px; padding: 2px 6px;
        border-radius: 2px; text-transform: uppercase; letter-spacing: 0.06em;
        font-family: 'Share Tech Mono', monospace; font-weight: 600; margin-top: 8px;
    }
    .h-pipeline-arrow {
        display: flex; align-items: center;
        padding: 0 4px; flex-shrink: 0; font-size: 14px;
    }

    /* ─── SVG Interactive Animations ─── */
    svg path {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }
    svg path:hover {
        filter: brightness(1.2) drop-shadow(0 0 8px var(--cyan));
        transform: scale(1.03);
        transform-origin: 65px 65px;
    }
    svg rect {
        transition: all 0.25s ease;
        cursor: pointer;
    }
    svg rect:hover {
        filter: brightness(1.2) drop-shadow(0 0 8px var(--cyan));
    }

    /* ─── Sidebar Pipeline (vertical) ─── */
    .pipeline-container { margin-top: 10px; margin-bottom: 10px; }
    .pipeline-step {
        display: flex; align-items: flex-start; gap: 10px;
        padding: 8px 10px; border-radius: 4px; margin-bottom: 5px;
        background: var(--bg-surface); border: 1px solid var(--ink-faint);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .pipeline-step:hover {
        transform: translateX(4px);
        border-color: var(--cyan-border);
        background: var(--cyan-glow);
        box-shadow: inset 3px 0 0 var(--cyan), 0 0 16px rgba(56,189,248,0.08);
    }
    .pipeline-step.active {
        background: rgba(56,189,248,0.08) !important;
        border-color: var(--cyan) !important;
        color: var(--cyan) !important;
        box-shadow: inset 3px 0 0 var(--cyan), 0 0 14px rgba(56,189,248,0.08) !important;
        animation: sb-glow-pulse 2.5s ease-in-out infinite !important;
    }
    .pipeline-step.done {
        background: rgba(59,130,246,0.08) !important;
        border-color: #3B82F6 !important;
        color: #3B82F6 !important;
        box-shadow: inset 3px 0 0 #3B82F6, 0 0 14px rgba(59,130,246,0.08) !important;
    }
    .step-number {
        display: flex; align-items: center; justify-content: center;
        width: 20px; height: 20px; border-radius: 50%;
        font-size: 9px; font-weight: 700; font-family: 'Share Tech Mono', monospace;
        background: #040A0C; border: 1px solid var(--ink-faint); flex-shrink: 0;
    }
    .pipeline-step.active .step-number { background: rgba(56,189,248,0.15); border-color: var(--cyan); color: var(--cyan); box-shadow: 0 0 8px rgba(56,189,248,0.3); }
    .pipeline-step.done .step-number { background: rgba(59,130,246,0.15); border-color: #3B82F6; color: #3B82F6; box-shadow: 0 0 8px rgba(59,130,246,0.3); }
    .step-name { font-size: 11.5px; font-weight: 600; color: var(--ink); }
    .step-desc { font-size: 9.5px; color: var(--ink-muted); margin-top: 1px; }

    /* ─── Buttons ─── */
    .stButton>button {
        background: transparent !important;
        border: 1px solid var(--ink-faint) !important;
        color: var(--ink-muted) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        border-radius: 4px !important;
        padding: 10px 20px !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    .stButton>button:hover {
        background: var(--cyan-glow) !important;
        border-color: var(--cyan-border) !important;
        color: var(--ink) !important;
    }
    .stButton>button::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 60% !important;
        height: 100% !important;
        background: linear-gradient(120deg, transparent, var(--cyan-glow), transparent) !important;
        transform: skewX(-20deg) !important;
        transition: left 0.5s ease !important;
    }
    .stButton>button:hover::before {
        left: 150% !important;
    }
    .stButton>button:active {
        transform: translateY(0) scale(0.98) !important;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: transparent !important;
        border: 1px solid var(--cyan) !important;
        color: var(--cyan) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 3px !important;
        border-radius: 4px !important;
        padding: 14px 28px !important;
        box-shadow: 0 0 16px var(--cyan-glow) !important;
        transition: all 0.15s ease !important;
        text-transform: uppercase !important;
        animation: pulse-cyan 3s ease-in-out infinite !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: var(--cyan-glow) !important;
        box-shadow: 0 0 30px var(--cyan-strong), inset 0 0 20px var(--cyan-glow) !important;
        text-shadow: 0 0 8px var(--cyan) !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important; text-align: center !important;
        background: rgba(56, 189, 248, 0.04) !important; border: 1px solid var(--cyan-border) !important;
        border-radius: 6px !important; padding: 0.8rem 1rem !important; margin-bottom: 0.4rem !important;
        font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important;
        font-size: 0.8rem !important; color: var(--cyan) !important; cursor: pointer !important;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        letter-spacing: 1.5px !important; text-transform: uppercase !important;
        position: relative !important; overflow: hidden !important;
    }
    [data-testid="stSidebar"] .stButton > button::before {
        content: "" !important; position: absolute !important;
        top: 0 !important; left: -100% !important; width: 60% !important; height: 100% !important;
        background: linear-gradient(120deg, transparent, rgba(56, 189, 248, 0.2), transparent) !important;
        transform: skewX(-20deg) !important;
        transition: left 0.5s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover::before { left: 150% !important; }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--cyan-glow) !important;
        border-color: var(--cyan) !important;
        color: var(--ink-bright) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px var(--cyan-strong) !important;
    }
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(0) scale(0.98) !important;
    }

    /* ─── Download Buttons ─── */
    .stDownloadButton > button {
        background: transparent !important;
        border: 1px solid var(--purple) !important;
        color: var(--purple) !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.8rem !important;
        font-weight: 400 !important;
        letter-spacing: 2px !important;
        border-radius: 4px !important;
        padding: 13px 24px !important;
        box-shadow: 0 0 12px rgba(139,92,246,0.1) !important;
        transition: all 0.15s ease !important;
        text-transform: uppercase !important;
        position: relative !important;
        overflow: hidden !important;
    }
    .stDownloadButton > button::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 60% !important;
        height: 100% !important;
        background: linear-gradient(120deg, transparent, rgba(139,92,246,0.15), transparent) !important;
        transform: skewX(-20deg) !important;
        transition: left 0.5s ease !important;
    }
    .stDownloadButton > button:hover::before {
        left: 150% !important;
    }
    .stDownloadButton > button:hover {
        background: var(--purple-dim) !important;
        box-shadow: 0 0 24px rgba(139,92,246,0.2) !important;
        color: var(--ink-bright) !important;
    }
    .stDownloadButton > button:active {
        transform: translateY(0) scale(0.98) !important;
    }

    /* ─── Inputs ─── */
    .stTextArea textarea {
        background-color: var(--bg-raised) !important;
        color: var(--ink) !important;
        border: 1px solid var(--ink-faint) !important;
        border-radius: 4px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.15s ease !important;
        caret-color: var(--cyan) !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--cyan-dim) !important;
        box-shadow: 0 0 14px var(--cyan-glow), inset 0 0 8px var(--cyan-glow) !important;
    }
    [data-testid="stFileUploader"] {
        background-color: var(--bg-raised) !important;
        border: 1px dashed var(--cyan-border) !important;
        border-radius: 4px !important;
        padding: 8px !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--cyan-strong) !important;
        background-color: var(--bg-hover) !important;
    }

    /* ─── Cards (stContainer) ─── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--cyan-border) !important;
        border-radius: 6px !important;
        padding: 1.25rem !important;
        box-shadow: 0 0 14px var(--cyan-glow) !important;
        margin-bottom: 1rem !important;
        transition: all 0.18s ease !important;
        animation: slide-up 0.35s ease-out;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--cyan-strong) !important;
        box-shadow: 0 0 20px var(--cyan-glow) !important;
    }

    /* ─── Evidence Quotes ─── */
    .evidence-quote {
        font-size: 13px; line-height: 1.55; color: var(--ink-muted); font-style: italic;
        background: var(--bg-surface); border-left: 3px solid var(--cyan);
        padding: 10px 14px; margin-bottom: 8px; border-radius: 0 4px 4px 0;
        transition: all 0.3s ease;
    }
    .evidence-quote:hover {
        border-left-width: 5px;
        background: var(--cyan-glow);
    }

    /* ─── Feedback Card ─── */
    .feedback-card {
        background: var(--bg-surface) !important;
        border: 1px solid var(--cyan-border) !important;
        border-radius: 4px !important;
        padding: 14px 16px !important;
        margin-bottom: 12px !important;
        transition: all 0.18s ease !important;
        animation: slide-up 0.3s ease-out backwards;
    }
    .feedback-card:hover {
        border-color: var(--cyan-strong) !important;
        box-shadow: 0 0 18px var(--cyan-glow) !important;
    }
    .feedback-card-support    { border-left: 3px solid var(--green) !important; }
    .feedback-card-support:hover { border-left-color: var(--green) !important; }
    .feedback-card-opposition { border-left: 3px solid var(--red) !important; }
    .feedback-card-opposition:hover { border-left-color: var(--red) !important; }
    .feedback-card-neutral    { border-left: 3px solid var(--ink-muted) !important; }
    .feedback-card-neutral:hover { border-left-color: var(--ink-muted) !important; }
    .feedback-avatar {
        width: 28px; height: 28px; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 700;
        background: var(--bg-raised); color: var(--cyan);
        flex-shrink: 0; margin-right: 8px; vertical-align: middle;
        border: 1px solid var(--cyan-border);
    }
    .feedback-author { font-size: 13px; font-weight: 600; color: var(--ink); }
    .feedback-role   { font-size: 11px; color: var(--ink-muted); margin-left: 6px; }
    .feedback-date   { font-size: 11px; color: var(--ink-faint); }
    .feedback-text   { font-size: 13px; color: var(--ink); line-height: 1.55; margin-top: 10px; }
    .feedback-tag {
        display: inline-block; font-size: 9px; padding: 2px 7px;
        border-radius: 2px; font-family: 'JetBrains Mono', monospace;
        font-weight: 500; background: var(--bg-raised); color: var(--ink-muted);
        margin-right: 4px; margin-top: 8px;
    }
    .sentiment-pill {
        display: inline-block; font-size: 10px; padding: 2px 8px;
        border-radius: 4px; font-family: 'Inter', sans-serif;
        font-weight: 500; text-transform: capitalize;
    }
    .sentiment-support    { background: var(--green-dim);  color: var(--green); border: 1px solid var(--green-dim); }
    .sentiment-opposition { background: var(--red-dim);    color: var(--red); border: 1px solid var(--red-dim); }
    .sentiment-neutral    { background: rgba(107, 127, 163, 0.08); color: var(--ink-muted); border: 1px solid rgba(107, 127, 163, 0.2); }

    /* ─── Executive Memo ─── */
    .memo-container {
        background: var(--bg-surface) !important; border: 1px solid var(--cyan-border) !important;
        border-radius: 4px !important; padding: 2.5rem !important;
        font-family: 'Inter', sans-serif !important; color: var(--ink) !important; line-height: 1.75 !important;
        transition: all 0.3s ease;
    }
    .memo-container:hover {
        border-color: var(--cyan-strong) !important;
        box-shadow: 0 0 20px var(--cyan-glow) !important;
    }
    .memo-letterhead {
        border-bottom: 1px solid var(--cyan-border);
        padding-bottom: 1rem; margin-bottom: 1.25rem;
        display: flex; justify-content: space-between; align-items: flex-end;
    }
    .memo-org {
        font-family: 'Space Grotesk', sans-serif; font-size: 11px;
        text-transform: uppercase; letter-spacing: 0.1em; color: var(--cyan); font-weight: 600;
    }
    .memo-date { font-size: 10px; color: var(--ink-muted); font-family: 'Inter', sans-serif; }

    /* ─── Tables ─── */
    table { width: 100%; border-collapse: collapse; color: var(--ink); }
    th {
        font-family: 'Space Grotesk', sans-serif; font-size: 10px;
        text-transform: uppercase; color: var(--ink-muted); letter-spacing: 0.06em;
        border-bottom: 1px solid var(--cyan-border) !important;
        padding: 8px 10px !important; text-align: left;
    }
    td { padding: 10px !important; border-bottom: 1px solid var(--ink-faint) !important; font-size: 12.5px; }
    tr:hover td { background-color: var(--bg-hover) !important; }

    /* ─── Tabs ─── */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--cyan-border); }
    .stTabs [data-baseweb="tab"] {
        background: transparent; border: none;
        padding: 8px 14px; color: var(--ink-muted);
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500; font-size: 13px;
        border-bottom: 2px solid transparent;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--cyan) !important;
        background: var(--cyan-glow) !important;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: var(--cyan) !important;
        border-bottom: 2px solid var(--cyan) !important;
    }

    /* ─── Expanders ─── */
    .stMain .streamlit-expanderHeader {
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--cyan-border) !important;
        border-radius: 4px !important; color: var(--ink) !important;
        transition: all 0.2s ease !important;
    }
    .stMain .streamlit-expanderHeader:hover {
        background-color: var(--bg-hover) !important;
        border-color: var(--cyan-strong) !important;
    }
    .stMain .streamlit-expanderContent {
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--cyan-border) !important;
        border-top: none !important; border-radius: 0 0 4px 4px !important;
    }

    /* ─── Survey Question Cards ─── */
    .survey-q-card {
        background: var(--bg-surface); border: 1px solid var(--cyan-border);
        border-left: 3px solid var(--purple) !important;
        border-radius: 4px; padding: 16px 18px; margin-bottom: 10px;
        transition: all 0.18s ease;
        animation: slide-up 0.3s ease-out backwards;
    }
    .survey-q-card:hover {
        border-color: var(--cyan-strong);
        border-left-color: var(--cyan);
        box-shadow: 0 0 18px var(--cyan-glow);
    }
    .survey-q-num {
        font-size: 9px; font-family: 'Space Grotesk', sans-serif;
        color: var(--cyan); text-transform: uppercase; letter-spacing: 0.08em;
        font-weight: 600; margin-bottom: 6px;
    }
    .survey-q-text { font-size: 13.5px; font-weight: 500; color: var(--ink); line-height: 1.45; margin-bottom: 8px; }
    .survey-q-type {
        display: inline-block; font-size: 9px; padding: 2px 7px;
        border-radius: 2px; font-family: 'Space Grotesk', sans-serif;
        font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .survey-q-option {
        font-size: 12px; color: var(--ink-muted);
        padding: 4px 0 4px 14px;
        border-left: 2px solid var(--ink-faint); margin-bottom: 2px;
        transition: all 0.2s ease;
    }
    .survey-q-option:hover {
        color: var(--ink);
        border-left-color: var(--cyan);
        padding-left: 16px;
    }

    /* ─── Landing Hero Elements ─── */
    .hero-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem 1rem 2.5rem 1rem;
        text-align: center;
        position: relative;
    }
    .master-badge-wrap {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1.6rem;
        animation: slide-up 0.5s ease-out backwards, float-y 4s ease-in-out infinite 0.8s;
        padding: 0 8px;
    }
    .master-badge {
        position: relative;
        display: inline-flex;
        align-items: center;
        gap: 14px;
        padding: 0.85rem 2.2rem;
        border-radius: 6px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(0.85rem, 2.4vw, 1.15rem);
        letter-spacing: 4px;
        text-transform: uppercase;
        color: var(--ink-bright);
        background: var(--bg-surface);
        border: 1px solid transparent;
        z-index: 1;
        animation: mega-glow 3s ease-in-out infinite;
        overflow: hidden;
    }
    .master-badge-wrap::before {
        content: ""; position: absolute; inset: -2px; border-radius: 8px;
        background: linear-gradient(90deg, var(--cyan), var(--purple), #3B82F6, var(--cyan));
        background-size: 200% 100%; animation: border-rotate 3s linear infinite; z-index: 0;
    }
    .master-badge-wrap::after {
        content: ""; position: absolute; inset: 0; border-radius: 6px;
        background: var(--bg-surface); z-index: 0; margin: 1px;
    }
    .master-badge-icon {
        color: var(--cyan); font-size: 1.1em;
        animation: rotate-slow 5s linear infinite; display: inline-block;
        text-shadow: 0 0 14px var(--cyan-glow); position: relative; z-index: 1;
    }
    .master-badge-text-1 { color: var(--ink-bright); }
    .master-badge-text-2 { color: var(--cyan); text-shadow: 0 0 16px var(--cyan-glow); }
    .master-badge-amp { color: var(--cyan); text-shadow: 0 0 12px var(--cyan-glow); animation: dot-blink 2s ease-in-out infinite; }
    .master-badge::before {
        content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(110deg, transparent 30%, var(--cyan-glow) 50%, transparent 70%);
        background-size: 200% 100%; animation: badge-shimmer 3s linear infinite;
        border-radius: 6px; pointer-events: none; z-index: 0;
    }
    .flow-strip {
        display: flex;
        align-items: stretch;
        gap: 0;
        width: 100%;
        animation: slide-up 0.7s ease-out 0.35s backwards;
    }
    .flow-card {
        background: var(--bg-surface);
        border: 1px solid var(--cyan-border);
        padding: 1.4rem 1.2rem;
        flex: 1;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        cursor: default;
        text-align: left;
    }
    .flow-card:nth-child(1) {
        border-top: 2px solid var(--cyan);
        border-radius: 6px 0 0 6px;
        animation: flow-card-lift 4s ease-in-out infinite 0s;
    }
    .flow-card:nth-child(3) {
        border-top: 2px solid var(--purple);
        animation: flow-card-lift 4s ease-in-out infinite 1.3s;
    }
    .flow-card:nth-child(5) {
        border-top: 2px solid #3B82F6;
        border-radius: 0 6px 6px 0;
        animation: flow-card-lift 4s ease-in-out infinite 2.6s;
    }
    .flow-card::before {
        content: ""; position: absolute; top: 0; left: -60%; width: 40%; height: 100%;
        background: linear-gradient(120deg, transparent, var(--cyan-glow), transparent);
        transform: skewX(-20deg); animation: badge-shimmer 4s linear infinite;
        pointer-events: none;
    }
    .flow-num {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.6rem;
        color: var(--ink-muted);
        letter-spacing: 2px;
        margin-bottom: 0.6rem;
        display: block;
        font-weight: 600;
    }
    .flow-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem;
        color: var(--ink-bright);
        margin-bottom: 0.4rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        animation: glow-pulse 5s ease-in-out infinite;
        font-weight: 600;
    }
    .flow-desc {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        color: var(--ink-muted);
        line-height: 1.55;
    }
    .flow-sep {
        width: 1px;
        background: var(--cyan-border);
        align-self: stretch;
    }
    .stat-strip {
        display: flex;
        gap: 1px;
        justify-content: center;
        width: 100%;
        background: var(--cyan-border);
        border: 1px solid var(--cyan-border);
        border-radius: 4px;
        overflow: hidden;
        animation: slide-up 0.7s ease-out 0.4s backwards;
    }
    .stat-pill {
        background: var(--bg-surface);
        padding: 1rem 1.4rem;
        text-align: center;
        flex: 1;
        cursor: default;
    }
    .stat-pill:nth-child(1) { animation: pulse-cyan 3s ease-in-out infinite 0s; }
    .stat-pill:nth-child(2) { animation: pulse-cyan 3s ease-in-out infinite 0.75s; }
    .stat-pill:nth-child(3) { animation: pulse-cyan 3s ease-in-out infinite 1.5s; }
    .stat-pill:nth-child(4) { animation: pulse-cyan 3s ease-in-out infinite 2.25s; }
    .stat-num {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.3rem;
        color: var(--cyan);
        display: inline-block;
        font-weight: 700;
        text-shadow: 0 0 14px var(--cyan-glow);
        animation: glow-pulse 3s ease-in-out infinite;
    }
    .stat-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.55rem;
        color: var(--ink-muted);
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 2px;
        display: block;
    }

    /* ─── Blinking Cursor ─── */
    .blinking-cursor {
        display: inline-block;
        width: 10px;
        margin-left: 4px;
        color: var(--cyan);
        animation: blink-cursor 1s steps(2, start) infinite;
    }

    /* ─── Scrollbar ─── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--cyan-dim); border-radius: 3px; }
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
if 'google_form_id' not in st.session_state:
    st.session_state['google_form_id'] = ""


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    # Logo
    st.markdown(
        '<div style="display:flex; align-items:center; gap:12px; padding: 12px 14px; background: rgba(56,189,248,0.03); border: 1px solid rgba(56,189,248,0.08); border-radius: 8px; margin-bottom: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">'
        '<div style="width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center;'
        ' background: linear-gradient(135deg, #38BDF8, #3B82F6); font-size:16px; box-shadow: 0 0 12px rgba(56,189,248,0.3); font-weight:700; color:#FFFFFF;">⬢</div>'
        '<div>'
        '<div style="font-family:\'Space Grotesk\', sans-serif; font-size:16px; font-weight:700; color:#E8EDF5; letter-spacing:-0.3px; line-height:1.15;">PolicyPulse AI</div>'
        '<div style="font-size:8.5px; text-transform:uppercase; color:#6B7FA3; letter-spacing:0.12em;'
        ' font-family:\'JetBrains Mono\', monospace; margin-top:2px;">Civic Intelligence</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Live indicator
    st.markdown(
        '<div style="display:flex; align-items:center; justify-content:center; gap:8px; padding:6px 12px; background: rgba(56,189,248,0.06); border: 1px solid rgba(56,189,248,0.15); border-radius: 20px; margin-bottom: 18px; width: fit-content; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'
        '<span style="position:relative; display:inline-flex; width:6px; height:6px;">'
        '<span style="position:absolute; display:inline-flex; width:100%; height:100%; border-radius:50%; background:#38BDF8; opacity:0.6; animation:ping 1.5s infinite;"></span>'
        '<span style="position:relative; display:inline-flex; width:6px; height:6px; border-radius:50%; background:#38BDF8;"></span>'
        '</span>'
        '<span style="font-size:9.5px; color:#38BDF8; font-family:\'Space Grotesk\', sans-serif; font-weight:600; letter-spacing:0.8px; text-transform:uppercase;">Live Analysis Engine</span>'
        '</div>'
        '<style>@keyframes ping{0%{transform:scale(1);opacity:0.7}75%,100%{transform:scale(2.2);opacity:0}}</style>',
        unsafe_allow_html=True
    )

    # API Key Check
    api_key_configured = bool(os.getenv("GROQ_API_KEY"))
    if not api_key_configured:
        st.error("⚠️ **Groq API Key Missing**\n\nAdd `GROQ_API_KEY` to your `.env` file.")

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
            if status == "Done":
                step_class = "pipeline-step done"
                badge_html = '<span class="badge badge-teal" style="font-size:7px; padding:1px 5px; margin-left:4px; vertical-align:middle;">Complete</span>'
            elif status == "Running":
                step_class = "pipeline-step active"
                badge_html = '<span class="badge badge-amber" style="font-size:7px; padding:1px 5px; margin-left:4px; vertical-align:middle;"><span class="status-dot-amber" style="width:4px; height:4px; margin-right:3px; display:inline-block; vertical-align:middle;"></span>Running</span>'
            elif status == "Optional":
                step_class = "pipeline-step"
                badge_html = '<span class="badge badge-blue" style="font-size:7px; padding:1px 5px; margin-left:4px; vertical-align:middle;">Optional</span>'
            else:
                step_class = "pipeline-step"
                badge_html = '<span class="badge badge-gray" style="font-size:7px; padding:1px 5px; margin-left:4px; vertical-align:middle;">Queued</span>'

            pipeline_html += (
                f'<div class="{step_class}">'
                f'<div class="step-number">{num}</div>'
                '<div>'
                f'<div class="step-name">{name} {badge_html}</div>'
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
# HEADER (Figma Top Bar)
# ==========================================
st.markdown(
    '<div class="figma-topbar">'
    '  <div>'
    '    <div class="figma-topbar-title">'
    '      Civic Intelligence Dashboard'
    '      <span class="figma-topbar-live">LIVE</span>'
    '    </div>'
    '    <div class="figma-topbar-sub">PolicyPulse AI &mdash; Multi-Agent Policy Analysis Engine</div>'
    '  </div>'
    '  <div class="figma-topbar-right">'
    '  </div>'
    '</div>',
    unsafe_allow_html=True
)

# ==========================================
# INPUT AREA
# ==========================================
if st.session_state['analysis_results'] is None and st.session_state['survey_results'] is None:
    st.markdown("""<div class="hero-wrapper">
<div class="master-badge-wrap">
<div class="master-badge">
<span class="master-badge-icon">⬢</span>
<span class="master-badge-text-1">PolicyPulse AI</span>
<span class="master-badge-amp">//</span>
<span class="master-badge-text-2">Civic Intelligence Engine</span>
</div>
</div>
<h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.2rem; font-weight: 700; color: var(--ink-bright); margin-bottom: 1rem; letter-spacing: -0.5px; line-height: 1.2;">
Consolidate Public Feedback. Audit Policy Gaps.<br/>
<span style="color: var(--cyan); text-shadow: 0 0 15px var(--cyan-glow);">Synthesize Actionable Strategy.</span><span class="blinking-cursor">|</span>
</h1>
<p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: var(--ink-muted); max-width: 600px; margin: 0 auto 2.5rem auto; line-height: 1.6;">
Transform policies and community comments into structured insights. Harness five specialized AI agents to discover hidden conflicts, align stakeholder values, and export demo-ready memos.
</p>
<!-- FLOW STRIP -->
<div class="flow-strip" style="margin-bottom: 2rem; max-width: 900px;">
<div class="flow-card">
<span class="flow-num">PHASE 01</span>
<div class="flow-title">1. Ingest & Parse</div>
<div class="flow-desc">Upload policy drafts and CSV/TXT public comments. Extract rule frameworks and parse stakeholder sentiment.</div>
</div>
<div class="flow-sep"></div>
<div class="flow-card">
<span class="flow-num">PHASE 02</span>
<div class="flow-title">2. Agent Synthesis</div>
<div class="flow-desc">Trigger five AI agents in parallel to cluster concerns, map severity matrices, and identify compliance gaps.</div>
</div>
<div class="flow-sep"></div>
<div class="flow-card">
<span class="flow-num">PHASE 03</span>
<div class="flow-title">3. Action Strategy</div>
<div class="flow-desc">Generate tailored recommendations, draft copyable executive memos, and output student/citizen survey templates.</div>
</div>
</div>
<!-- STATS STRIP -->
<div class="stat-strip" style="max-width: 900px; margin-bottom: 1.5rem;">
<div class="stat-pill">
<div class="stat-num">5</div>
<div class="stat-label">AI Agents Active</div>
</div>
<div class="stat-pill">
<div class="stat-num">100%</div>
<div class="stat-label">Local Demo Safe</div>
</div>
<div class="stat-pill">
<div class="stat-num">Zero</div>
<div class="stat-label">DB Dependency</div>
</div>
<div class="stat-pill">
<div class="stat-num">&lt; 10s</div>
<div class="stat-label">Analysis Time</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

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

        # Fetch comments from Google Form Responses
        st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.06); margin:12px 0;"></div>', unsafe_allow_html=True)
        st.caption("⚡ Or fetch live responses from your deployed Google Form:")
        
        form_id_input = st.text_input("Google Form ID", value=st.session_state['google_form_id'], key="form_id_sync_input", label_visibility="collapsed", placeholder="Enter Google Form ID...")
        
        if st.button("📥 Fetch Google Form Responses", use_container_width=True):
            if not form_id_input.strip():
                st.warning("Please enter a valid Google Form ID.")
            else:
                with st.spinner("Fetching live comments from Google Sheets via Apps Script..."):
                    fetch_res = survey_agent.fetch_form_responses(form_id_input.strip())
                    if fetch_res.get("csv"):
                        csv_data = fetch_res["csv"]
                        try:
                            import pandas as pd
                            import io
                            df = pd.read_csv(io.StringIO(csv_data))
                            
                            # Search for comments column
                            target_col = None
                            possible_columns = ['comment', 'comments', 'feedback', 'text', 'review', 'reviews', 'response', 'responses', 'content', 'message', 'messages']
                            normalized_cols = {col.lower().strip(): col for col in df.columns}
                            for col_name in possible_columns:
                                if col_name in normalized_cols:
                                    target_col = normalized_cols[col_name]
                                    break
                            
                            # Fallback to last column or any string column if not found
                            if target_col is None and not df.empty:
                                string_cols = [c for c in df.columns if df[c].dtype == object]
                                string_cols = [c for c in string_cols if c.lower() != 'timestamp']
                                if string_cols:
                                    target_col = string_cols[0]
                                else:
                                    target_col = df.columns[-1]
                            
                            if target_col and not df.empty:
                                comments_list = df[target_col].dropna().astype(str).tolist()
                                st.session_state['demo_comments'] = "\n".join(comments_list)
                                st.success(f"Successfully loaded {len(comments_list)} responses from Google Sheets!")
                                st.rerun()
                            else:
                                st.session_state['demo_comments'] = csv_data
                                st.success("Loaded raw responses successfully!")
                                st.rerun()
                        except Exception as parse_err:
                            st.session_state['demo_comments'] = csv_data
                            st.success("Loaded responses as raw text!")
                            st.rerun()
                    else:
                        st.error(f"Failed to fetch responses: {fetch_res.get('error')}")

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
    notification_box.success("✅ Multi-agent consultation pipeline synthesis complete!")
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
                import traceback
                traceback.print_exc()
                status_box.empty()
                st.error(f"Execution failed: {e}")
                st.code(traceback.format_exc())

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
            ("Public Support", f"{support_pct}%", "#38BDF8", "📈"),
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

        # ─── Charts Row (Figma exact: 2fr donut | 3fr bar) ───
        def make_donut_svg(support_pct, opposition_pct, neutral_pct):
            import math
            data = [
                ("Support",    support_pct,    "#38BDF8"),
                ("Opposition", opposition_pct, "#EF4444"),
                ("Neutral",    neutral_pct,    "#6B7FA3"),
            ]
            cx, cy, r, inner_r, gap = 65, 65, 52, 33, 2
            total = sum(v for _, v, _ in data)
            angle = -90.0
            paths = []
            for name, value, color in data:
                sweep = (value / total * 360) - gap if total else 0
                start = angle + gap / 2
                end = start + sweep
                angle += value / total * 360 if total else 0
                large = 1 if sweep > 180 else 0
                def pt(a, rad):
                    return (cx + rad * math.cos(math.radians(a)),
                            cy + rad * math.sin(math.radians(a)))
                x1,y1 = pt(start, r); x2,y2 = pt(end, r)
                x3,y3 = pt(end, inner_r); x4,y4 = pt(start, inner_r)
                d = f"M {x1:.2f} {y1:.2f} A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f} L {x3:.2f} {y3:.2f} A {inner_r} {inner_r} 0 {large} 0 {x4:.2f} {y4:.2f} Z"
                paths.append((name, color, d, value))

            svg = f'<svg width="130" height="130" viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">'
            for _, color, d, _ in paths:
                svg += f'<path d="{d}" fill="{color}" />'
            svg += '</svg>'

            legend = ''
            for name, color, _, value in paths:
                legend += (
                    f'<div class="donut-legend-item">'
                    f'<div class="donut-legend-left">'
                    f'<div class="donut-dot" style="background:{color};"></div>'
                    f'<span class="donut-legend-label">{name}</span>'
                    f'</div>'
                    f'<span class="donut-legend-value">{value}%</span>'
                    f'</div>'
                )

            html = (
                f'<div class="chart-card" style="margin-bottom:0;">'
                f'<div class="chart-header">'
                f'<div><div class="figma-card-title">Sentiment Distribution</div>'
                f'<div class="figma-card-sub">Analyzed across stakeholder feedback</div></div>'
                f'<span class="chart-header-badge">30D</span>'
                f'</div>'
                f'<div class="donut-row">{svg}<div class="donut-legend">{legend}</div></div>'
                f'</div>'
            )
            return html

        def make_bar_svg(gaps_list):
            if not gaps_list:
                return ''
            # Build per-gap data
            gap_bars = []
            for g in gaps_list[:8]:
                concern = sanitize_html(str(g.get('concern', g.get('gap', 'Gap'))))[:22]
                sev = g.get('severity', 'Medium')
                sev_lower = str(sev).lower()
                if any(x in sev_lower for x in ['critical', 'high']):
                    color = '#EF4444'; sev_label = 'High'
                elif 'low' in sev_lower:
                    color = '#3B82F6'; sev_label = 'Low'
                else:
                    color = '#F59E0B'; sev_label = 'Medium'
                gap_bars.append((concern, color, sev_label))

            n = len(gap_bars)
            w, h = 420, 130
            pad_l, pad_b, pad_t, pad_r = 8, 28, 8, 8
            chart_w = w - pad_l - pad_r
            chart_h = h - pad_t - pad_b
            bar_w = max(18, int(chart_w / n) - 10)
            max_val = n  # each bar is height relative to count=1 since these are boolean gaps

            # Instead use a count-based chart: severity counts
            sev_counts = {'High': 0, 'Medium': 0, 'Low': 0}
            for _, _, sl in gap_bars:
                sev_counts[sl] += 1
            bar_data = [(k, v, '#EF4444' if k=='High' else '#F59E0B' if k=='Medium' else '#3B82F6')
                        for k, v in sev_counts.items() if v > 0]
            n = len(bar_data)
            if n == 0:
                return ''
            max_val = max(v for _, v, _ in bar_data)
            bar_w2 = int(chart_w / n) - 16
            grid_vals = [0, max_val // 2, max_val] if max_val > 1 else [0, max_val]

            svg = f'<svg width="100%" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="overflow:visible">'
            # grid lines
            for v in grid_vals:
                y = pad_t + chart_h - (v / max_val * chart_h if max_val else 0)
                svg += f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="rgba(255,255,255,0.04)" stroke-dasharray="3 3"/>'
                svg += f'<text x="{pad_l-2}" y="{y+3.5:.1f}" text-anchor="end" font-size="8" fill="#4A6080" font-family="JetBrains Mono">{v}</text>'
            # bars
            slot_w = chart_w / n
            for i, (label, val, color) in enumerate(bar_data):
                x = pad_l + i * slot_w + (slot_w - bar_w2) / 2
                bar_h2 = (val / max_val * chart_h) if max_val else 0
                y = pad_t + chart_h - bar_h2
                svg += f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w2}" height="{bar_h2:.1f}" fill="{color}" rx="3"/>'
                words = label.split()
                for wi, word in enumerate(words):
                    ly = h - 14 + wi * 9
                    svg += f'<text x="{x + bar_w2/2:.1f}" y="{ly}" text-anchor="middle" font-size="8" fill="#4A6080" font-family="JetBrains Mono">{word}</text>'
            svg += '</svg>'

            legend_items = [
                ('<div class="bar-legend-swatch" style="background:#EF4444;"></div> High Severity'),
                ('<div class="bar-legend-swatch" style="background:#F59E0B;"></div> Medium Severity'),
                ('<div class="bar-legend-swatch" style="background:#3B82F6;"></div> Low Severity'),
            ]
            legend_html = ''.join(f'<div class="bar-legend-item">{li}</div>' for li in legend_items)

            html = (
                f'<div class="chart-card" style="margin-bottom:0;">'
                f'<div class="chart-header">'
                f'<div><div class="figma-card-title">Policy Gaps by Severity</div>'
                f'<div class="figma-card-sub">Identified coverage deficiencies</div></div>'
                f'<span class="chart-header-link">View all &rsaquo;</span>'
                f'</div>'
                f'{svg}'
                f'<div class="bar-legend">{legend_html}</div>'
                f'</div>'
            )
            return html

        donut_html = make_donut_svg(support_pct, opposition_pct, neutral_pct)
        bar_html = make_bar_svg(gaps_list)

        st.markdown(
            f'<div class="charts-row">{donut_html}{bar_html}</div>',
            unsafe_allow_html=True
        )
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

            html = '<div style="background:var(--bg-surface); border:1px solid var(--cyan-border); border-radius:12px; padding:18px 16px; margin-bottom:1rem; box-shadow: 0 0 16px var(--cyan-glow);">'
            html += '<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;">'
            html += '<div><div class="figma-card-title">Multi-Agent Analysis Pipeline</div>'
            html += '<div class="figma-card-sub" style="margin-bottom:0;">Sequential AI processing chain</div></div>'

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

                icon_class = "h-pipeline-icon rotate-slow" if status == "Running" else "h-pipeline-icon"
                dot_html = ""
                if status == "Done":
                    dot_html = '<span class="status-dot-blue" style="margin-left:4px;"></span>'
                elif status == "Running":
                    dot_html = '<span class="status-dot-amber" style="margin-left:4px;"></span>'
                else:
                    dot_html = '<span class="h-pipeline-dot" style="background:var(--ink-faint); margin-left:4px;"></span>'

                name_color = "var(--ink-bright)" if status in ["Done", "Running"] else "var(--ink-muted)"
                badge_class = "badge badge-teal" if status == "Done" else "badge badge-amber" if status == "Running" else "badge badge-blue" if status == "Optional" else "badge badge-gray"
                badge_text = "Complete" if status == "Done" else "Running" if status == "Running" else "Optional" if status == "Optional" else "Queued"

                html += '<div class="h-pipeline-step">'
                html += f'<div class="h-pipeline-card {card_class}">'
                html += f'<div><span class="{icon_class}">{icon}</span>{dot_html}</div>'
                html += f'<div class="h-pipeline-name" style="color:{name_color};">{name}</div>'
                html += f'<div class="h-pipeline-desc">{desc}</div>'
                html += f'<span class="{badge_class}" style="font-size:8px; padding:2px 6px; margin-top:8px;">{badge_text}</span>'
                html += '</div>'

                if i < len(steps_def) - 1:
                    arrow_class = "h-pipeline-arrow arrow-flow" if status in ["Done", "Running"] else "h-pipeline-arrow"
                    arrow_color = "#3B82F6" if status == "Done" else "var(--amber)" if status == "Running" else "var(--ink-faint)"
                    html += f'<div class="{arrow_class}" style="color:{arrow_color}; font-size: 16px; align-self: center;">→</div>'

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
                        color_continuous_scale=['#1E3A8A', '#38BDF8']
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
                        type_bg = "rgba(56,189,248,0.10)" if q_type == "multiple_choice" else "rgba(245,158,11,0.10)" if q_type == "rating" else "rgba(59,130,246,0.10)"
                        type_color = "#38BDF8" if q_type == "multiple_choice" else "#F59E0B" if q_type == "rating" else "#3B82F6"
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
                        if result.get("form_id"):
                            st.session_state['google_form_id'] = result.get("form_id")
                            st.markdown(f"**🔑 Form ID:** `{result['form_id']}` *(populated in Comment syncing widget above)*")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        st.error(f"Form creation failed: {error_msg}")
        else:
            st.info("Click 'Generate Feedback Survey Blueprint' to create a structured Google Forms setup blueprint based on your loaded policy document.")
