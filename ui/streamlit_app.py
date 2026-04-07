"""
Kapruka Gift-Concierge - Premium Modern UI v3
==============================================
Run with:  streamlit run ui/streamlit_app.py

CUSTOMIZE THE PREBUILT SUGGESTION PILLS
─────────────────────────────────────────
Search for the section marked:
    # ── ✏️  EDIT SUGGESTION PILLS HERE ──
to change the quick-start prompts shown on the welcome screen.

CUSTOM BACKGROUND IMAGE
────────────────────────
Drop a PNG/JPG into  ui/static/  and update BG_IMAGE_PATH below.
Set BG_IMAGE_PATH = None  to disable the custom background.
"""

import sys
import base64
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# ─────────────────────────────────────────────────────────────
# 🖼️  CUSTOM BACKGROUND IMAGES
BG_DARK_PATH  = Path(__file__).parent / "static" / "bg_dark_kapruka.png"
BG_LIGHT_PATH = Path(__file__).parent / "static" / "bg_light_kapruka.png"
# ─────────────────────────────────────────────────────────────

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Kapruka Gift-Concierge",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme toggle ─────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True  # default: dark

is_dark = st.session_state.dark_mode

# ── Load background image as base64 ──────────────────────────
def _load_bg(path: Path) -> str | None:
    try:
        if path and path.exists():
            data = path.read_bytes()
            b64  = base64.b64encode(data).decode()
            ext  = path.suffix.lstrip(".")
            return f"data:image/{ext};base64,{b64}"
    except Exception:
        pass
    return None

BG_DATA_URL = _load_bg(BG_DARK_PATH) if is_dark else _load_bg(BG_LIGHT_PATH)

# ── CSS variables ─────────────────────────────────────────────
DARK_VARS = """
  --bg:           #0A0E1A;
  --bg2:          #111827;
  --bg3:          #1A2235;
  --fg:           #F0F4FF;
  --fg2:          #8892A4;
  --fg3:          #5C6B84;
  --border:       #1E2D45;
  --border2:      #253552;
  --accent:       #FF7043;
  --accent2:      #FF9800;
  --accent-glow:  rgba(255,112,67,0.25);
  --blue:         #4F8EF7;
  --green:        #10B981;
  --red:          #EF4444;
  --yellow:       #F59E0B;
  --pink:         #EC4899;
  --card-bg:      rgba(17,24,39,0.80);
  --glass:        rgba(255,255,255,0.04);
  --nav-blur:     rgba(10,14,26,0.90);
  --user-bubble:  linear-gradient(135deg,#FF7043,#FF9800);
  --user-text:    #FFFFFF;
  --input-bg:     rgba(26,34,53,0.9);
  --input-bd:     #253552;
  --shadow-sm:    0 2px 12px rgba(0,0,0,0.45);
  --shadow-md:    0 8px 32px rgba(0,0,0,0.55);
  --shadow-glow:  0 0 24px rgba(255,112,67,0.2);
"""

LIGHT_VARS = """
  --bg:           #F0F4FF;
  --bg2:          #FFFFFF;
  --bg3:          #E8EEFF;
  --fg:           #0F172A;
  --fg2:          #475569;
  --fg3:          #94A3B8;
  --border:       #E2E8F0;
  --border2:      #CBD5E1;
  --accent:       #FF7043;
  --accent2:      #FF9800;
  --accent-glow:  rgba(255,112,67,0.15);
  --blue:         #3B82F6;
  --green:        #10B981;
  --red:          #EF4444;
  --yellow:       #F59E0B;
  --pink:         #EC4899;
  --card-bg:      #FFFFFF;
  --glass:        rgba(255,255,255,0.75);
  --nav-blur:     rgba(240,244,255,0.92);
  --user-bubble:  linear-gradient(135deg,#FF7043,#FF9800);
  --user-text:    #FFFFFF;
  --input-bg:     #FFFFFF;
  --input-bd:     #CBD5E1;
  --shadow-sm:    0 2px 12px rgba(0,0,0,0.07);
  --shadow-md:    0 8px 32px rgba(0,0,0,0.12);
  --shadow-glow:  0 0 24px rgba(255,112,67,0.15);
"""

st.markdown(
    f"<style>:root {{ { DARK_VARS if is_dark else LIGHT_VARS } }}</style>",
    unsafe_allow_html=True,
)

# ── Background image injection ──────────────────────────────
bg_overlay = "rgba(10,14,26,0.55)" if is_dark else "rgba(240,244,255,0.60)"

if BG_DATA_URL:
    st.markdown(f"""
<style>
.stApp {{
    background-image: url("{BG_DATA_URL}") !important;
    background-size: cover !important;
    background-position: center center !important;
    background-attachment: fixed !important;
}}
/* Overlay so text stays readable */
.stApp::before {{
    content: '';
    position: fixed; inset: 0;
    background: {bg_overlay};
    z-index: 0;
    pointer-events: none;
}}
</style>
""", unsafe_allow_html=True)

# ── Main CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    box-sizing: border-box;
}
.stApp { background-color: var(--bg) !important; }

/* ── Hide Streamlit chrome & force transparent containers ── */
#MainMenu, footer, header, [data-testid="stHeader"] { visibility: hidden; background: transparent !important; }
[data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], 
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { 
    background-color: transparent !important; 
    background: transparent !important; 
}
div[class^="stBottom"], div[class^="stAppView"] { 
    background-color: transparent !important; 
    background: transparent !important; 
}
[data-testid="stBottom"] > div { background: transparent !important; }

.block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 18px; padding-left: 14px; padding-right: 14px;
}

.brand-wrap { display:flex; align-items:center; gap:12px; padding:4px 0 18px; }
.brand-logo {
    width:42px; height:42px; border-radius:12px; flex-shrink:0;
    background: linear-gradient(135deg,#FF7043 0%,#FF9800 100%);
    display:flex; align-items:center; justify-content:center;
    font-size:20px;
    box-shadow: 0 4px 16px rgba(255,112,67,0.4), inset 0 1px 0 rgba(255,255,255,0.2);
}
.brand-name { font-size:15px; font-weight:700; color:var(--fg); letter-spacing:-0.3px; }
.brand-sub  { font-size:11px; color:var(--fg2); margin-top:2px; }
.s-divider  { height:1px; background:var(--border); margin:12px 0; border:none; }
.s-label    { font-size:10px; font-weight:700; color:var(--fg3); text-transform:uppercase; letter-spacing:1.2px; margin:0 0 10px; }
.s-stat     { display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:var(--glass); border:1px solid var(--border); border-radius:10px; margin-bottom:6px; }
.s-stat-label { font-size:12px; color:var(--fg2); }
.s-stat-val   { font-size:12px; font-weight:600; color:var(--fg); }
.pill-allergy { display:inline-block; font-size:10.5px; font-weight:600; background:rgba(239,68,68,0.12); color:#F87171; border:1px solid rgba(239,68,68,0.25); border-radius:20px; padding:3px 10px; margin:2px 3px 2px 0; }
.pill-pref    { display:inline-block; font-size:10.5px; font-weight:600; background:rgba(79,142,247,0.12); color:var(--blue); border:1px solid rgba(79,142,247,0.25); border-radius:20px; padding:3px 10px; margin:2px 3px 2px 0; }
.profile-row  { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.profile-key  { font-size:12px; color:var(--fg2); }
.profile-val  { font-size:12px; font-weight:600; color:var(--fg); text-align:right; max-width:58%; }
.empty-recipient { background:var(--glass); border:1px dashed var(--border2); border-radius:14px; padding:20px; text-align:center; }
.empty-recipient .ri { font-size:28px; margin-bottom:8px; }
.empty-recipient .rt { font-size:12px; color:var(--fg3); line-height:1.5; }

/* ── Sidebar buttons ── */
.stButton > button {
    background: var(--glass) !important; color:var(--fg) !important;
    border:1px solid var(--border) !important; border-radius:10px !important;
    font-size:13px !important; font-weight:500 !important;
    padding:9px 16px !important; width:100% !important;
    transition:all 0.2s ease !important; box-shadow:none !important;
    margin-bottom:6px !important;
}
.stButton > button:hover {
    background:var(--bg3) !important; border-color:var(--accent) !important;
    color:var(--accent) !important;
    box-shadow:0 0 0 3px var(--accent-glow) !important;
}

/* ── Top nav ── */
.top-nav {
    position:sticky; top:0; z-index:200;
    background:var(--nav-blur); backdrop-filter:blur(24px); -webkit-backdrop-filter:blur(24px);
    border-bottom:1px solid var(--border);
    padding:0 40px; height:60px;
    display:flex; align-items:center; justify-content:space-between;
    margin:-16px -16px 0 -16px;
}
.nav-brand { font-size:16px; font-weight:700; color:var(--fg); letter-spacing:-0.4px; }
.nav-left  { display:flex; align-items:center; gap:12px; }
.nav-live  {
    display:flex; align-items:center; gap:5px;
    font-size:11px; font-weight:600; color:var(--green);
    background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.25);
    border-radius:20px; padding:4px 10px;
}
.nav-live::before {
    content:''; width:6px; height:6px; background:var(--green);
    border-radius:50%; display:inline-block; animation:pulse 2s infinite;
}
.nav-right { font-size:11px; color:var(--fg3); }
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.5; transform:scale(0.85); }
}

/* ── Welcome screen ── */
.welcome-outer {
    display:flex; flex-direction:column; align-items:center;
    justify-content:center; padding:70px 24px 150px;
    min-height:72vh; position:relative; z-index:1;
}
.welcome-glow {
    width:80px; height:80px; border-radius:24px;
    background:linear-gradient(135deg,#FF7043 0%,#FF9800 55%,#FFC107 100%);
    box-shadow:0 16px 48px rgba(255,112,67,0.5), 0 0 0 1px rgba(255,255,255,0.08);
    display:flex; align-items:center; justify-content:center;
    font-size:36px; margin-bottom:28px;
    animation:float 3.5s ease-in-out infinite;
}
@keyframes float {
    0%,100% { transform:translateY(0); }
    50%      { transform:translateY(-10px); }
}
.welcome-title {
    font-size:34px; font-weight:800; color:var(--fg);
    letter-spacing:-1px; margin-bottom:12px; text-align:center;
}
.welcome-title span {
    background:linear-gradient(135deg,#FF7043,#FF9800);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.welcome-sub {
    font-size:16px; color:var(--fg2); max-width:460px; text-align:center;
    line-height:1.7; margin-bottom:42px; font-weight:400;
}
.suggestion-grid {
    display:flex; flex-wrap:wrap; gap:10px;
    justify-content:center; max-width:640px;
}
.s-pill {
    background:var(--card-bg); border:1px solid var(--border2);
    border-radius:24px; padding:11px 20px; font-size:13px;
    color:var(--fg); cursor:pointer;
    transition:all 0.2s ease; font-weight:500;
    box-shadow:var(--shadow-sm);
    backdrop-filter:blur(8px);
}
.s-pill:hover {
    border-color:var(--accent);
    box-shadow:0 4px 20px var(--accent-glow);
    transform:translateY(-2px); color:var(--accent);
}
.feature-strip  { display:flex; gap:8px; flex-wrap:wrap; justify-content:center; margin-top:32px; }
.f-badge {
    display:flex; align-items:center; gap:5px;
    font-size:11px; font-weight:600; padding:5px 12px;
    border-radius:20px; color:var(--fg2);
    background:var(--glass); border:1px solid var(--border);
    backdrop-filter:blur(8px);
}

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 6px 0 !important;
}

/* ── ALL text in chat defaults to theme foreground ── */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] {
    color: var(--fg) !important;
    font-size: 14px;
    line-height: 1.75;
}

/* ── USER bubble (orange gradient, right-aligned feel) ── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #FF7043, #FF9800) !important;
    border-radius: 20px 20px 6px 20px !important;
    padding: 12px 18px !important;
    box-shadow: 0 4px 20px rgba(255,112,67,0.35) !important;
    max-width: 78%;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] p {
    color: #FFFFFF !important;
    font-weight: 500;
}

/* ── ASSISTANT bubble (glass card, theme-aware) ── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px 20px 20px 20px !important;
    padding: 16px 20px !important;
    box-shadow: var(--shadow-md) !important;
    backdrop-filter: blur(16px) !important;
    max-width: 88%;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] li {
    color: var(--fg) !important;
    font-size: 14px;
    line-height: 1.8;
}

/* ── Intent chip ── */
.intent-chip {
    display:inline-flex; align-items:center; gap:6px;
    font-size:11px; font-weight:700; padding:4px 12px;
    border-radius:20px; margin:6px 0 12px; letter-spacing:0.3px;
}
.chip-search  { background:rgba(79,142,247,0.12); color:#4F8EF7; border:1px solid rgba(79,142,247,0.3); }
.chip-deliver { background:rgba(245,158,11,0.12); color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }
.chip-pref    { background:rgba(16,185,129,0.12); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
.chip-history { background:rgba(236,72,153,0.12); color:#EC4899; border:1px solid rgba(236,72,153,0.3); }
.chip-general { background:rgba(148,163,184,0.12); color:#94A3B8; border:1px solid rgba(148,163,184,0.3); }

/* ── Product cards ── */
.product-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:14px; margin:14px 0; }
.product-card {
    background:var(--card-bg); border:1px solid var(--border);
    border-radius:16px; padding:18px; transition:all 0.25s ease;
    box-shadow:var(--shadow-sm); position:relative; overflow:hidden;
    backdrop-filter:blur(8px);
}
.product-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:linear-gradient(90deg,#FF7043,#FF9800,#FFC107);
    opacity:0; transition:opacity 0.25s;
}
.product-card:hover { border-color:var(--accent); box-shadow:var(--shadow-md); transform:translateY(-3px); }
.product-card:hover::before { opacity:1; }
.pc-name  { font-size:13px; font-weight:700; color:var(--fg); margin-bottom:6px; line-height:1.4; }
.pc-price { font-size:20px; font-weight:800; color:var(--accent); margin-bottom:8px; }
.pc-meta  { font-size:11px; color:var(--fg2); margin-bottom:10px; font-weight:500; }
.pc-tags  { display:flex; flex-wrap:wrap; gap:4px; margin-top:4px; }
.tag-safe    { display:inline-block; font-size:10px; font-weight:600; background:rgba(16,185,129,0.12); color:#10B981; border:1px solid rgba(16,185,129,0.3); border-radius:12px; padding:2px 8px; }
.tag-allergy { display:inline-block; font-size:10px; font-weight:600; background:rgba(239,68,68,0.12); color:#F87171; border:1px solid rgba(239,68,68,0.3); border-radius:12px; padding:2px 8px; }
.pc-bar  { height:4px; background:var(--border); border-radius:4px; margin-top:12px; overflow:hidden; }
.pc-fill { height:100%; border-radius:4px; background:linear-gradient(90deg,#FF7043,#FF9800); }
.pc-score-label { font-size:10px; color:var(--fg3); margin-top:4px; }
.pc-buy-btn { display:block; text-align:center; background:linear-gradient(135deg,#FF7043,#FF9800); color:#FFF !important; text-decoration:none; font-size:12px; font-weight:700; padding:8px 0; border-radius:8px; margin-top:12px; transition:transform 0.2s, box-shadow 0.2s; }
.pc-buy-btn:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(255,112,67,0.3); }

/* ── Reflection log ── */
.refl-card { background:var(--glass); border:1px solid var(--border); border-radius:12px; padding:14px 16px; margin:8px 0; }
.refl-iter { font-size:10px; font-weight:700; color:var(--fg3); text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; }
.refl-pass { color:#10B981; font-weight:700; }
.refl-fail { color:#F87171; font-weight:700; }
.refl-row  { font-size:12px; color:var(--fg); margin-bottom:5px; }

/* ── Latency tag ── */
.latency-tag {
    display:inline-flex; align-items:center; gap:4px;
    font-size:10.5px; color:var(--fg3); margin-top:10px;
    padding:3px 8px; background:var(--glass);
    border-radius:8px; border:1px solid var(--border);
}

/* ── Chat input ── */
[data-testid="stChatInputContainer"] {
    background: transparent !important;
    border: none !important;
    backdrop-filter: none !important;
    padding: 14px 40px !important;
    position: relative !important; z-index: 100 !important;
}
[data-testid="stChatInput"] {
    background:var(--input-bg) !important;
    border:1.5px solid var(--input-bd) !important;
    border-radius:16px !important; font-size:14px !important;
    padding:13px 18px !important; color:var(--fg) !important;
    box-shadow:var(--shadow-sm) !important; transition:all 0.2s ease !important;
}
[data-testid="stChatInput"]:focus {
    border-color:var(--accent) !important;
    box-shadow:0 0 0 4px var(--accent-glow), var(--shadow-sm) !important;
    outline:none !important;
}
[data-testid="stChatInput"]::placeholder { color:var(--fg3) !important; }

/* ── Suggestion pill BUTTONS ── */
/* Target the Streamlit button elements inside the pill container */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button,
div.pill-row div[data-testid="stButton"] > button {
    background: var(--card-bg) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 24px !important;
    padding: 11px 20px !important;
    font-size: 13px !important;
    color: var(--fg) !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    font-weight: 500 !important;
    box-shadow: var(--shadow-sm) !important;
    backdrop-filter: blur(8px) !important;
    width: 100% !important;
    white-space: normal !important;
    height: auto !important;
    line-height: 1.4 !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:hover,
div.pill-row div[data-testid="stButton"] > button:hover {
    border-color: var(--accent) !important;
    box-shadow: 0 4px 20px var(--accent-glow) !important;
    transform: translateY(-2px) !important;
    color: var(--accent) !important;
    background: var(--glass) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] > details > summary {
    background:var(--glass) !important; border:1px solid var(--border) !important;
    border-radius:10px !important; font-size:13px !important;
    font-weight:600 !important; color:var(--fg) !important;
    padding:12px 16px !important;
}
[data-testid="stExpander"] {
    border:1px solid var(--border) !important;
    border-radius:12px !important;
    background:var(--glass) !important;
    margin-bottom:8px !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
    color:var(--fg2) !important;
    font-size:13px !important;
    line-height:1.7 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--border2); border-radius:3px; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────
def init_session():
    for k, v in {
        "agent": None,
        "messages": [],
        "last_response": None,
        "agent_error": None,
        "agent_loading": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


def load_agent():
    """Load the GiftConciergeAgent - shows a spinner on first load."""
    if st.session_state.agent is not None or st.session_state.agent_error:
        return  # already loaded or errored

    with st.spinner("🔮 Initialising AI concierge - loading embedding model…"):
        try:
            from src.orchestrator import GiftConciergeAgent
            st.session_state.agent = GiftConciergeAgent()
            st.session_state.agent_error = None
        except Exception as e:
            st.session_state.agent_error = str(e)


init_session()


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class='brand-wrap'>
      <div class='brand-logo'>🎁</div>
      <div>
        <div class='brand-name'>Gift-Concierge</div>
        <div class='brand-sub'>Kapruka.com · AI Advisor</div>
      </div>
    </div>
    <div class='s-divider'></div>
    """, unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state.page = "agent"

    if st.button("🤖  Agent Chat", key="btn_nav_agent"):
        st.session_state.page = "agent"
        st.rerun()

    if st.button("❓  Help & FAQ", key="btn_nav_faq"):
        st.session_state.page = "faq"
        st.rerun()

    if st.button("＋  New Conversation", key="btn_new"):
        if st.session_state.agent:
            st.session_state.agent.reset_session()
        st.session_state.messages = []
        st.session_state.last_response = None
        st.session_state.page = "agent"
        st.rerun()

    if st.button("☀️  Light Mode" if is_dark else "🌙  Dark Mode", key="btn_theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown("<div class='s-divider'></div>", unsafe_allow_html=True)

    # Recipient profile
    last = st.session_state.last_response
    if last and last.get("recipient") and st.session_state.agent:
        rk      = last["recipient"]
        profile = st.session_state.agent.memory.semantic.get_profile(rk)
        if profile:
            st.markdown("<p class='s-label'>Recipient Profile</p>", unsafe_allow_html=True)
            rows = ""
            for lbl, val in [("Name", profile.get("name","-")), ("Location", profile.get("location","-"))]:
                rows += f"<div class='profile-row'><span class='profile-key'>{lbl}</span><span class='profile-val'>{val}</span></div>"
            st.markdown(rows, unsafe_allow_html=True)

            if profile.get("allergies"):
                pills = "".join(f"<span class='pill-allergy'>⚠ {a}</span>" for a in profile["allergies"])
                st.markdown(f"<p class='s-label' style='margin-top:12px'>Allergies</p>{pills}", unsafe_allow_html=True)

            if profile.get("preferences"):
                pills = "".join(f"<span class='pill-pref'>{p}</span>" for p in profile["preferences"][:4])
                st.markdown(f"<p class='s-label' style='margin-top:12px'>Preferences</p>{pills}", unsafe_allow_html=True)

            if profile.get("past_gifts"):
                st.markdown("<p class='s-label' style='margin-top:12px'>Past Gifts</p>", unsafe_allow_html=True)
                for g in profile["past_gifts"][-3:]:
                    st.markdown(f"<div class='profile-row'><span class='profile-key'>{g['item']}</span><span class='profile-val'>{g.get('occasion','')}</span></div>", unsafe_allow_html=True)

            if profile.get("budget_range_lkr"):
                b = profile["budget_range_lkr"]
                st.markdown(f"<div class='s-stat' style='margin-top:8px'><span class='s-stat-label'>Budget</span><span class='s-stat-val'>LKR {b.get('min',0):,} – {b.get('max',0):,}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='s-label'>Recipient</p>", unsafe_allow_html=True)
        st.markdown("""
        <div class='empty-recipient'>
          <div class='ri'>👤</div>
          <div class='rt'>Mention a recipient and their profile will appear here</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='s-divider'></div>", unsafe_allow_html=True)
    st.markdown("<p class='s-label'>Session</p>", unsafe_allow_html=True)
    if st.session_state.agent:
        try:
            summary = st.session_state.agent.get_session_summary()
            for lbl, val in [
                ("Messages",   summary["messages_in_context"]),
                ("Recipients", len(summary["recipients_known"])),
                ("Catalog",    "✓ Indexed" if summary.get("catalog_loaded") else "⚠ Run ingest"),
            ]:
                st.markdown(f"<div class='s-stat'><span class='s-stat-label'>{lbl}</span><span class='s-stat-val'>{val}</span></div>", unsafe_allow_html=True)
        except Exception:
            pass
    else:
        st.markdown("<div class='s-stat'><span class='s-stat-label'>Status</span><span class='s-stat-val'>Initialising…</span></div>", unsafe_allow_html=True)

    st.markdown("<div class='s-divider'></div>", unsafe_allow_html=True)
    st.markdown("<p class='s-label'>Powered by</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:11px; color:var(--fg3); line-height:2; padding:0 2px;'>
      🤖 Anthropic Claude<br>
      🗄️ Qdrant Vector DB<br>
      🧠 all-MiniLM-L6-v2<br>
      ⚡ Pure Python - No Frameworks
    </div>""", unsafe_allow_html=True)


# ── TOP NAV ───────────────────────────────────────────────────
st.markdown("""
<div class='top-nav'>
  <div class='nav-left'>
    <span class='nav-brand'>🎁 Kapruka Gift-Concierge</span>
    <span class='nav-live'>Live</span>
  </div>
  <span class='nav-right'>Claude · Qdrant · Sri Lanka 🇱🇰</span>
</div>
""", unsafe_allow_html=True)


# ── Load agent (with spinner) ─────────────────────────────────
load_agent()

if st.session_state.agent_error:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error(
        f"⚠️ **Agent failed to load:**\n\n```\n{st.session_state.agent_error}\n```\n\n"
        "**Checklist:**\n"
        "- Verify `.env` contains `ANTHROPIC_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`\n"
        "- Run `python setup_ingest.py` to populate the vector catalog"
    )
    if st.button("🔄 Retry", key="btn_retry"):
        st.session_state.agent = None
        st.session_state.agent_error = None
        st.rerun()
    st.stop()


# ── INTENT CHIP ───────────────────────────────────────────────
CHIP_MAP = {
    "PRODUCT_SEARCH":    ("chip-search",   "🔍 Product Search"),
    "DELIVERY_CHECK":    ("chip-deliver",  "🚚 Delivery Check"),
    "PREFERENCE_UPDATE": ("chip-pref",     "✏️ Preference Update"),
    "ORDER_HISTORY":     ("chip-history",  "🕑 Order History"),
    "GENERAL":           ("chip-general",  "💬 General"),
}

def make_chip(intent: str) -> str:
    cls, label = CHIP_MAP.get(intent, ("chip-general", intent))
    return f"<span class='intent-chip {cls}'>{label}</span>"


# ── PRODUCT CARDS ─────────────────────────────────────────────
def make_product_cards(products: list) -> str:
    cards = ""
    for hit in products[:3]:
        p      = hit["product"]
        raw_score = hit.get("score", 0.0)
        # Scale score up for better UI display since all-MiniLM outputs tight bounds
        score_pct = int(min(100, max(0, (raw_score * 100) if raw_score > 0.1 else raw_score * 1000)))
        
        allergens = p.get("contains_allergens", [])
        tags      = p.get("tags", [])

        tag_html = ""
        if allergens:
            tag_html += "".join(f"<span class='tag-allergy'>⚠ {a}</span>" for a in allergens)
        else:
            tag_html += "<span class='tag-safe'>✓ Allergen-free</span>"
        tag_html += "".join(f"<span class='tag-safe'>{t}</span>" for t in tags[:2])

        import urllib.parse
        encoded_name = urllib.parse.quote(p['product_name'])
        safe_url = f"https://www.kapruka.com/sri_lanka_search.jsp?searchWord={encoded_name}"
        
        cards += f"""
        <div class='product-card'>
          <div class='pc-name'>{p['product_name']}</div>
          <div class='pc-price'>LKR {p['price_lkr']:,.0f}</div>
          <div class='pc-meta'>{p.get('category','').replace('-',' ').title()} · {p.get('delivery_type','').title()}</div>
          <div class='pc-tags'>{tag_html}</div>
          <div class='pc-bar'><div class='pc-fill' style='width:{score_pct}%'></div></div>
          <div class='pc-score-label'>Match score {score_pct}%</div>
          <a href="{safe_url}" target="_blank" class='pc-buy-btn'>🛒 Search on Kapruka</a>
        </div>"""
    return f"<div class='product-grid'>{cards}</div>"


# ── FAQ PAGE ──────────────────────────────────────────────────
if st.session_state.page == "faq":
    st.markdown("""
    <style>
    /* ── FAQ premium layout ── */
    .faq-hero {
        background: var(--bg2);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 44px 40px 36px;
        margin: 8px 0 0;
        position: relative;
        overflow: hidden;
    }
    .faq-hero::after {
        content: '';
        position: absolute;
        top: -80px; right: -80px;
        width: 260px; height: 260px;
        background: radial-gradient(circle, rgba(255,112,67,0.12) 0%, transparent 70%);
        pointer-events: none;
    }
    .faq-hero-eyebrow {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 11px; font-weight: 700; letter-spacing: 1.2px;
        text-transform: uppercase; color: var(--accent);
        background: rgba(255,112,67,0.1); border: 1px solid rgba(255,112,67,0.25);
        border-radius: 20px; padding: 4px 12px; margin-bottom: 18px;
    }
    .faq-hero-title {
        font-size: 30px; font-weight: 800; color: var(--fg);
        letter-spacing: -0.8px; line-height: 1.15; margin-bottom: 10px;
    }
    .faq-hero-title span {
        background: linear-gradient(135deg,#FF7043,#FF9800);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .faq-hero-sub {
        font-size: 14px; color: var(--fg2); line-height: 1.65;
        max-width: 500px; margin-bottom: 28px;
    }
    .faq-stats {
        display: flex; gap: 10px; flex-wrap: wrap;
    }
    .faq-stat {
        display: flex; align-items: center; gap: 7px;
        background: var(--glass); border: 1px solid var(--border);
        border-radius: 10px; padding: 7px 14px;
        font-size: 12px; font-weight: 600; color: var(--fg2);
    }
    /* category header */
    .faq-cat {
        display: flex; align-items: center; gap: 10px;
        margin: 32px 0 10px;
    }
    .faq-cat-icon {
        width: 32px; height: 32px; border-radius: 9px;
        display: flex; align-items: center; justify-content: center;
        font-size: 15px; flex-shrink: 0;
    }
    .faq-cat-title {
        font-size: 12px; font-weight: 700; color: var(--fg);
        text-transform: uppercase; letter-spacing: 0.9px;
    }
    .faq-cat-badge {
        font-size: 10.5px; font-weight: 600; color: var(--fg3);
        background: var(--glass); border: 1px solid var(--border);
        border-radius: 20px; padding: 2px 9px;
    }
    .faq-divider { height: 1px; background: var(--border); margin: 6px 0 4px; }
    /* expander overrides scoped to FAQ */
    .faq-wrap [data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        background: var(--card-bg) !important;
        margin-bottom: 5px !important;
        transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
    }
    .faq-wrap [data-testid="stExpander"]:hover {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    .faq-wrap [data-testid="stExpander"] summary,
    .faq-wrap .streamlit-expanderHeader {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 13px 18px !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        color: var(--fg) !important;
    }
    .faq-wrap [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    .faq-wrap [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
        color: var(--fg2) !important;
        font-size: 13px !important;
        line-height: 1.78 !important;
        padding-bottom: 2px !important;
    }
    .faq-wrap [data-testid="stExpander"] [data-testid="stMarkdownContainer"] code {
        background: var(--glass) !important;
        border: 1px solid var(--border) !important;
        border-radius: 5px !important;
        padding: 1px 6px !important;
        font-size: 12px !important;
        color: var(--accent) !important;
    }
    /* CTA card */
    .faq-cta {
        background: linear-gradient(135deg, rgba(255,112,67,0.07) 0%, rgba(255,152,0,0.07) 100%);
        border: 1px solid rgba(255,112,67,0.22);
        border-radius: 16px;
        padding: 28px 32px;
        margin-top: 36px;
        display: flex; align-items: center; justify-content: space-between;
        flex-wrap: wrap; gap: 16px;
    }
    .faq-cta h3 { font-size: 15px; font-weight: 700; color: var(--fg); margin-bottom: 4px; }
    .faq-cta p  { font-size: 13px; color: var(--fg2); margin: 0; }
    </style>
    """, unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────────
    st.markdown("""
    <div class='faq-hero'>
      <div class='faq-hero-eyebrow'>❓ Help Center</div>
      <div class='faq-hero-title'>Everything you need to know<br>about your <span>AI Gift Advisor</span></div>
      <div class='faq-hero-sub'>
        Browse answers by topic below. If you still need help,
        switch to Agent Chat and ask directly.
      </div>
      <div class='faq-stats'>
        <div class='faq-stat'>📖 10 answers</div>
        <div class='faq-stat'>🇱🇰 Sri Lanka focused</div>
        <div class='faq-stat'>🛡️ Allergen safe</div>
        <div class='faq-stat'>🧠 AI-powered memory</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='faq-wrap'>", unsafe_allow_html=True)

    # ── Category: Getting Started ─────────────────────────────
    st.markdown("""
    <div class='faq-cat'>
      <div class='faq-cat-icon' style='background:rgba(79,142,247,0.12);'>🚀</div>
      <span class='faq-cat-title'>Getting Started</span>
      <span class='faq-cat-badge'>3 topics</span>
    </div>
    <div class='faq-divider'></div>
    """, unsafe_allow_html=True)
    with st.expander("What is Kapruka Gift-Concierge?"):
        st.markdown(
            "An AI-powered gift advisor built on top of **Kapruka.com** — Sri Lanka's largest online gift store. "
            "It recommends gifts matched to your recipient's tastes, checks allergen safety, verifies delivery "
            "availability across all 25 districts, and remembers every recipient's profile across conversations."
        )
    with st.expander("How do I find a gift?"):
        st.markdown(
            "Type naturally in the chat — for example:\n\n"
            "> *\"Birthday cake for my wife under LKR 5,000 — she is nut-free\"*\n\n"
            "The agent searches the product catalog, filters unsafe allergens, and surfaces the top matches "
            "with prices, allergen tags, and a direct buy link to Kapruka."
        )
    with st.expander("What currency are prices shown in?"):
        st.markdown(
            "All prices are in **Sri Lankan Rupees (LKR)**. Include a budget in your message — "
            "e.g. *\"under LKR 3,000\"* or *\"around LKR 8,000\"* — and the agent will filter accordingly."
        )

    # ── Category: Allergen & Safety ───────────────────────────
    st.markdown("""
    <div class='faq-cat'>
      <div class='faq-cat-icon' style='background:rgba(239,68,68,0.12);'>🛡️</div>
      <span class='faq-cat-title'>Allergen &amp; Safety</span>
      <span class='faq-cat-badge'>2 topics</span>
    </div>
    <div class='faq-divider'></div>
    """, unsafe_allow_html=True)
    with st.expander("Which allergens does the agent check for?"):
        st.markdown(
            "The agent screens every recommendation against these allergens:\n\n"
            "**Nuts · Dairy · Gluten · Eggs · Soy · Shellfish · Fish**\n\n"
            "Mention any allergy in your message and all unsafe products are automatically excluded. "
            "Products are tagged with ✓ Allergen-free or ⚠ contains allergen in the results."
        )
    with st.expander("Can I update allergen info for a recipient?"):
        st.markdown(
            "Yes — just say it conversationally:\n\n"
            "> *\"My daughter is now allergic to dairy\"*\n\n"
            "The agent updates the recipient's profile immediately and applies the restriction "
            "to all future recommendations for that person."
        )

    # ── Category: Delivery & Locations ────────────────────────
    st.markdown("""
    <div class='faq-cat'>
      <div class='faq-cat-icon' style='background:rgba(245,158,11,0.12);'>🚚</div>
      <span class='faq-cat-title'>Delivery &amp; Locations</span>
      <span class='faq-cat-badge'>2 topics</span>
    </div>
    <div class='faq-divider'></div>
    """, unsafe_allow_html=True)
    with st.expander("Which districts are covered?"):
        st.markdown(
            "All **25 districts** of Sri Lanka are supported — Colombo, Kandy, Galle, Jaffna, "
            "Matara, Anuradhapura, Kurunegala, Ratnapura, Badulla, Trincomalee, and more. "
            "Just mention the district or city in your message."
        )
    with st.expander("How do I check if delivery is available?"):
        st.markdown(
            "Ask directly:\n\n"
            "> *\"Can you deliver a chocolate cake to Kandy on Saturday?\"*\n\n"
            "The agent checks delivery feasibility for that district and product type and confirms instantly."
        )

    # ── Category: Memory & Profiles ───────────────────────────
    st.markdown("""
    <div class='faq-cat'>
      <div class='faq-cat-icon' style='background:rgba(16,185,129,0.12);'>🧠</div>
      <span class='faq-cat-title'>Memory &amp; Profiles</span>
      <span class='faq-cat-badge'>2 topics</span>
    </div>
    <div class='faq-divider'></div>
    """, unsafe_allow_html=True)
    with st.expander("How does recipient memory work?"):
        st.markdown(
            "When you mention a recipient by name — e.g. *\"my wife Priya\"* or *\"thaththa\"* — "
            "the agent builds a profile that stores their allergies, preferences, typical budget, "
            "and past gift history. This profile is **persisted across conversations** and recalled "
            "automatically next time you mention the same person."
        )
    with st.expander("How do I start a new conversation?"):
        st.markdown(
            "Click **＋ New Conversation** in the sidebar. This clears the current chat session. "
            "Saved recipient profiles in long-term memory are **not** cleared — they carry over "
            "to all future conversations."
        )

    # ── Category: Troubleshooting ─────────────────────────────
    st.markdown("""
    <div class='faq-cat'>
      <div class='faq-cat-icon' style='background:rgba(236,72,153,0.12);'>⚙️</div>
      <span class='faq-cat-title'>Troubleshooting</span>
      <span class='faq-cat-badge'>1 topic</span>
    </div>
    <div class='faq-divider'></div>
    """, unsafe_allow_html=True)
    with st.expander("Why did the agent fail to load?"):
        st.markdown(
            "Check three things:\n\n"
            "1. Your `.env` file has valid `ANTHROPIC_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY`\n"
            "2. The Qdrant instance is reachable at the URL you configured\n"
            "3. You've run `python setup_ingest.py` at least once to populate the vector catalog\n\n"
            "Once fixed, click **🔄 Retry** on the error screen to reload without restarting."
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── CTA ───────────────────────────────────────────────────
    st.markdown("""
    <div class='faq-cta'>
      <div>
        <h3>Still have questions?</h3>
        <p>The AI concierge can answer anything about gifts, delivery, and recipient preferences.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🤖  Go to Agent Chat", key="faq_go_chat", use_container_width=False):
        st.session_state.page = "agent"
        st.rerun()


# ── WELCOME SCREEN or CHAT HISTORY ───────────────────────────
elif not st.session_state.messages:
    # ─────────────────────────────────────────────────────────
    # ── ✏️  EDIT SUGGESTION PILLS HERE ──────────────────────
    # These are the quick-start prompts shown on the welcome
    # screen. Change the text between the quotes to customise.
    # ─────────────────────────────────────────────────────────
    SUGGESTIONS = [
        "🎂 Birthday cake for my wife (nut-free), LKR 5,000",
        "🌸 Flowers for amma under LKR 3,000",
        "🚚 Can you deliver a cake to Kandy on Saturday?",
        "💡 My daughter is allergic to dairy",
        "🎉 Avurudu gift ideas for thaththa",
        "🔁 What did I send my wife last Valentine's?",
    ]
    # ─────────────────────────────────────────────────────────

    st.markdown("""
    <div class='welcome-outer'>
      <div class='welcome-glow'>🎁</div>
      <div class='welcome-title'>Your <span>AI Gift Advisor</span><br>for Sri Lanka</div>
      <div class='welcome-sub'>
        Personalized gift recommendations with allergen safety,
        delivery checks across all 25 districts, and long-term recipient memory.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Render clickable pill buttons in a 2-column grid
    col1, col2 = st.columns(2)
    for i, suggestion in enumerate(SUGGESTIONS):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(suggestion, key=f"pill_{i}", use_container_width=True):
                st.session_state["pending_prompt"] = suggestion
                st.rerun()

    st.markdown("""
      <div class='feature-strip' style='margin-top:24px;'>
        <div class='f-badge'>🛡️ Allergen Safety</div>
        <div class='f-badge'>🧠 3-Tier Memory</div>
        <div class='f-badge'>🗺️ 25 Districts</div>
        <div class='f-badge'>🔄 Reflection Loop</div>
        <div class='f-badge'>🇱🇰 Sri Lanka-Aware</div>
      </div>
    """, unsafe_allow_html=True)

else:  # agent page with messages
    st.markdown("<div style='padding:16px 0 150px;'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if msg["role"] == "assistant" and msg.get("meta"):
                meta   = msg["meta"]
                intent = meta.get("intent", "")

                st.markdown(make_chip(intent), unsafe_allow_html=True)

                products = meta.get("products_recommended", [])
                if products:
                    st.markdown(make_product_cards(products), unsafe_allow_html=True)

                refl = meta.get("reflection_log")
                if refl:
                    status = meta.get("safety_status", "SAFE")
                    icon   = "✅" if status == "SAFE" else "⚠️" if status == "SAFE_WITH_WARNINGS" else "🚨"
                    with st.expander(f"{icon} Safety Reflection - {len(refl)} iteration{'s' if len(refl)>1 else ''}", expanded=False):
                        for entry in refl:
                            it       = entry.get("iteration","?")
                            critique = entry.get("critique", {})
                            allergen = critique.get("allergen_check","N/A")
                            passed   = entry.get("all_passed", False)
                            ac = "refl-pass" if allergen == "PASS" else "refl-fail"
                            st.markdown(f"""
                            <div class='refl-card'>
                              <div class='refl-iter'>Iteration {it}</div>
                              <div class='refl-row'>Allergen: <span class='{ac}'>{allergen}</span></div>
                              <div class='refl-row'>Preference: {critique.get('preference_check','N/A')}</div>
                              <div class='refl-row'>Budget: {critique.get('budget_check','N/A')}</div>
                              <div class='refl-row'>All passed: {"<span class='refl-pass'>Yes ✓</span>" if passed else "<span class='refl-fail'>No - revised</span>"}</div>
                            </div>""", unsafe_allow_html=True)
                            for v in critique.get("allergen_violations", []):
                                st.error(f"⛔ {v}")

                if meta.get("metadata"):
                    lat   = meta["metadata"].get("latency_ms","")
                    model = meta["metadata"].get("model_used","")
                    st.markdown(f"<div class='latency-tag'>⏱ {lat} ms · {model}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── CHAT INPUT (agent page only) ─────────────────────────────
if st.session_state.page != "agent":
    st.stop()

# Consume a pill click (pending_prompt) OR a manual typed message
_pending = st.session_state.pop("pending_prompt", None)
prompt   = _pending or st.chat_input("Ask me to find a gift, check delivery, or update preferences…")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt, "meta": None})

    with st.chat_message("assistant"):
        with st.spinner("Finding the perfect gift…"):
            try:
                response = st.session_state.agent.chat(prompt)
                st.session_state.last_response = response
                reply    = response["response"].replace(" - ", " - ").replace("-", "-")
                st.markdown(reply)
                st.session_state.messages.append({
                    "role": "assistant", "content": reply, "meta": response
                })
            except Exception as e:
                err = f"Something went wrong: {e}"
                st.error(err)
                st.session_state.messages.append({
                    "role": "assistant", "content": err, "meta": None
                })
    st.rerun()
