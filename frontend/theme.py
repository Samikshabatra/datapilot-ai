"""DataPilot AI visual theme for the Streamlit app.

Translates the Stitch "DataPilot AI" design (glassmorphism, electric-purple/blue
accents, Inter type, dotted-grid + ambient-glow background) into CSS that restyles
Streamlit's components. Pure presentation — no behaviour changes.
"""
from __future__ import annotations

import streamlit as st

# Palette (from the design's DESIGN.md)
PRIMARY = "#d0bcff"        # electric purple
SECONDARY = "#adc6ff"      # deep blue accent
SECONDARY_CONTAINER = "#0566d9"
ON_SURFACE = "#e7e0ed"
ON_SURFACE_VARIANT = "#cbc3d7"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

/* ---- Global: pure-black canvas, dotted grid, ambient corner glows ---- */
.stApp {
  background-color: #050505;
  background-image:
    radial-gradient(circle at 0% 0%, rgba(109,59,215,0.18) 0%, transparent 42%),
    radial-gradient(circle at 100% 100%, rgba(5,102,217,0.16) 0%, transparent 42%),
    radial-gradient(rgba(208,188,255,0.10) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 24px 24px;
  background-attachment: fixed;
}
html, body, [class*="css"], .stApp, button, input, textarea, select {
  font-family: 'Inter', sans-serif !important;
}
h1, h2, h3 { letter-spacing: -0.02em !important; font-weight: 600 !important; color: #e7e0ed !important; }

/* ---- Brand header ---- */
.dp-brand { display:flex; align-items:center; gap:.6rem; margin: .2rem 0 .1rem; }
.dp-logo {
  font-size: 1.7rem; font-weight: 900; line-height: 1;
  background: linear-gradient(90deg, #d0bcff, #adc6ff);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.dp-pill {
  font-size: 10px; letter-spacing: .16em; font-weight: 700; text-transform: uppercase;
  color: #d0bcff; background: rgba(208,188,255,0.10);
  border: 1px solid rgba(208,188,255,0.30); padding: 2px 8px; border-radius: 999px;
}
.dp-h1 { font-size: 2.6rem; font-weight: 600; letter-spacing: -0.02em; margin: .35rem 0 .35rem; color: #fff; }
.dp-sub { color: #cbc3d7; opacity: .8; font-size: 1.05rem; max-width: 760px; margin-bottom: .4rem; }

/* ---- Sidebar: glass panel ---- */
[data-testid="stSidebar"] > div:first-child {
  background: rgba(255,255,255,0.035);
  backdrop-filter: blur(14px);
  border-right: 1px solid rgba(255,255,255,0.10);
}

/* ---- Buttons: gradient + glow (primary), used for st.button/download ---- */
.stButton > button, .stDownloadButton > button {
  background: linear-gradient(90deg, #d0bcff 0%, #0566d9 100%);
  color: #23005c; font-weight: 600; border: none; border-radius: 12px;
  box-shadow: 0 0 16px rgba(208,188,255,0.28); transition: all .18s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  color: #1a0044; box-shadow: 0 0 24px rgba(208,188,255,0.5); transform: translateY(-1px);
}
.stButton > button:active, .stDownloadButton > button:active { transform: scale(.98); }

/* ---- Chat messages: glass cards ---- */
[data-testid="stChatMessage"] {
  background: rgba(255,255,255,0.035);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px; padding: 1rem 1.2rem; margin-bottom: .4rem;
}

/* ---- Expanders: glass ---- */
[data-testid="stExpander"] {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; backdrop-filter: blur(8px); overflow: hidden;
}
[data-testid="stExpander"] summary:hover { color: #d0bcff; }

/* ---- Chat input: glass pill with neon edge ---- */
[data-testid="stChatInput"] {
  background: rgba(21,18,27,0.55);
  border: 1px solid rgba(208,188,255,0.28);
  border-radius: 18px; backdrop-filter: blur(12px);
  box-shadow: 0 0 20px rgba(208,188,255,0.08);
}
[data-testid="stChatInput"] textarea { color: #e7e0ed !important; }
[data-testid="stChatInput"] button { color: #d0bcff !important; }

/* ---- Code blocks: deep black, soft border ---- */
pre, .stCode, [data-testid="stCode"] {
  background: #0a0a0a !important; border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px;
}
code { font-family: 'JetBrains Mono', monospace !important; }

/* ---- File uploader dropzone: dashed purple ---- */
[data-testid="stFileUploaderDropzone"] {
  background: rgba(208,188,255,0.05);
  border: 2px dashed rgba(208,188,255,0.28); border-radius: 14px;
}

/* ---- Dataframes & tables ---- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; overflow: hidden;
}

/* ---- Alerts: rounded glass ---- */
[data-testid="stAlert"] { border-radius: 14px; backdrop-filter: blur(8px); }

/* ---- Image (charts) framing ---- */
[data-testid="stImage"] img { border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); }

/* ---- Scrollbar ---- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.22); }

/* hide default Streamlit chrome for a cleaner look */
#MainMenu, footer { visibility: hidden; }
</style>
"""

_HEADER = """
<div class="dp-brand">
  <span class="dp-logo">DataPilot AI</span>
  <span class="dp-pill">Pro</span>
</div>
<div class="dp-h1">Autonomous Data Analyst</div>
<div class="dp-sub">Upload data, ask questions in natural language, and let AI analyze your
datasets with professional statistical precision — every answer shows the code it ran.</div>
"""


def apply_theme() -> None:
    """Inject the global CSS. Call once, right after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header() -> None:
    """Render the gradient DataPilot AI brand header."""
    st.markdown(_HEADER, unsafe_allow_html=True)
